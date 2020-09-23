import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, COMPUTER_CASE, POWER_SUPPLY, \
    RAM, MONITOR, MOUSE, VIDEO_CARD, PROCESSOR, MOTHERBOARD, \
    KEYBOARD, CPU_COOLER, SOLID_STATE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class HardGaming(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            COMPUTER_CASE,
            POWER_SUPPLY,
            RAM,
            SOLID_STATE_DRIVE,
            MONITOR,
            MOUSE,
            VIDEO_CARD,
            PROCESSOR,
            MOTHERBOARD,
            KEYBOARD,
            CPU_COOLER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['gabinete', COMPUTER_CASE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['memorias', RAM],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['teclados', KEYBOARD],
            ['refrigeracion', CPU_COOLER],
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
                url_webpage = 'https://www.hardgaming.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                base_url_store = 'https://www.hardgaming.cl'
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(base_url_store + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-form_title page-title').text
        sku = soup.find('span', 'sku_elem').text.strip()
        if sku == '':
            return []
        stock_container = soup.find('form', 'product-form form-horizontal'). \
            find('div',
                 'form-group product-stock product-out-stock text-center '
                 'hidden')
        if not stock_container:
            stock = 0
        else:
            stock = -1
        normal_price = Decimal(
            remove_words(soup.find('span', 'product-form_price').text))
        offer_price = normal_price
        picture_containers = soup.find('div', 'owl-thumbs product-page-thumbs '
                                              'overflow-hidden '
                                              'mt-3')
        if not picture_containers:
            picture_urls = [soup.find('div', 'product-images owl-carousel '
                                             'product-slider').find('img')[
                                'src'].split('?')[0]]
        else:
            picture_urls = [tag['src'].split('?')[0] for tag in
                            picture_containers.findAll('img')]
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
