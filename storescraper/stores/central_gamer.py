import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, COMPUTER_CASE, CPU_COOLER, \
    POWER_SUPPLY, MONITOR, HEADPHONES, MOUSE, KEYBOARD, GAMING_CHAIR, \
    PROCESSOR, VIDEO_CARD, VIDEO_GAME_CONSOLE, STORAGE_DRIVE, GAMING_DESK, \
    MICROPHONE, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class CentralGamer(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            COMPUTER_CASE,
            CPU_COOLER,
            POWER_SUPPLY,
            MONITOR,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            GAMING_CHAIR,
            PROCESSOR,
            VIDEO_CARD,
            VIDEO_GAME_CONSOLE,
            STORAGE_DRIVE,
            GAMING_DESK,
            MICROPHONE,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento', STORAGE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes-gamer', COMPUTER_CASE],
            ['placas-madre-pc', MOTHERBOARD],
            ['todo-para-pc-gamer/refrigeracion', CPU_COOLER],
            ['tarjetas-de-video', VIDEO_CARD],
            ['audifonos-gamer', HEADPHONES],
            ['monitores-gamers', MONITOR],
            ['mouses-gamer', MOUSE],
            ['teclados-gamer', KEYBOARD],
            ['sillas-gamer-y-alfombras', GAMING_CHAIR],
            ['procesadores', PROCESSOR],
            ['escritorios-gamer', GAMING_DESK],
            ['microfonos-streamer-gamer', MICROPHONE],
            ['todo-para-pc-gamer/refrigeracion/ventiladores-para-gabinete',
             CASE_FAN],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.centralgamer.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div',
                                                  'col-lg-3 col-md-4 col-6')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.centralgamer.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-form_title').text
        sku = soup.find('form', 'product-form')['action'].split('/')[-1]

        stock_tag = soup.find('meta', {'property': 'product:availability'})
        if stock_tag['content'] == 'instock':
            stock = -1
        else:
            stock = 0

        price_tags = soup.findAll('span', {'id': 'product-form-price'})

        if len(price_tags) == 2:
            offer_price = Decimal(remove_words(price_tags[0].text))
            normal_price = Decimal(remove_words(price_tags[1].text))
        elif len(price_tags) == 1:
            offer_price = Decimal(remove_words(price_tags[0].text))
            normal_price = offer_price
        else:
            raise Exception('Invalid price tags')

        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'product-images').findAll('img')]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
