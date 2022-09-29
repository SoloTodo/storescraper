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
                                                  'product-block__wrapper')
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

        if 'Lo sentimos, no pudimos encontrar esa página' in soup.text:
            return []

        name = soup.find('h1', 'product-heading__title').text
        form = soup.find('form', 'product-form')
        if form:
            key = form['action'].split('/')[-1]
        else:
            key = soup.find('meta', {'property': 'og:id'})['content']
        span_sku = soup.find('span', 'product-heading__detail--sku')
        if span_sku:
            sku = span_sku.text.replace('SKU: ', '')
        else:
            sku = None

        stock_tag = soup.find('meta', {'property': 'product:availability'})
        if stock_tag['content'] == 'instock':
            stock = -1
        else:
            stock = 0

        price_tags = soup.findAll('h2', 'product-heading__pricing')

        if len(price_tags) % 2 == 0:
            if 'product-heading__pricing--has-discount' in \
                    price_tags[0]['class']:
                offer_price = Decimal(remove_words(
                    price_tags[0].find('span').text))
                normal_price = Decimal(remove_words(
                    price_tags[1].find('span').text))
            else:
                offer_price = Decimal(remove_words(price_tags[0].text))
                normal_price = Decimal(remove_words(price_tags[1].text))
        elif len(price_tags) % 1 == 1:
            if 'product-heading__pricing--has-discount' in \
                    price_tags[0]['class']:
                offer_price = Decimal(remove_words(
                    price_tags[0].find('span').text))
            else:
                offer_price = Decimal(remove_words(price_tags[0].text))
            normal_price = offer_price
        else:
            raise Exception('Invalid price tags')

        picture_slider = soup.find('div', 'product-gallery__slider')
        if picture_slider:
            picture_urls = [tag['src'].split('?')[0] for tag in
                            picture_slider.findAll('img')]
        else:
            picture_urls = [
                soup.find('div', 'product-gallery').find('img')['data-src']]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls
        )
        return [p]
