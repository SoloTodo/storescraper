import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PROCESSOR, NOTEBOOK, HEADPHONES, MOUSE, \
    KEYBOARD, STORAGE_DRIVE, SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    RAM, MOTHERBOARD, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class ComercialNet(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computadores-y-tablets/notebook', NOTEBOOK],
            ['computadores-y-tablets/headsets', HEADPHONES],
            ['computadores-y-tablets/mouses-y-teclados/mouse', MOUSE],
            ['computadores-y-tablets/mouses-y-teclados/categoria-1', KEYBOARD],
            ['componentes-y-partes/almacenamiento/hdd', STORAGE_DRIVE],
            ['componentes-y-partes/almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['componentes-y-partes/fuentes-de-poder-psu/', POWER_SUPPLY],
            ['/componentes-y-partes/gabinetes', COMPUTER_CASE],
            ['componentes-y-partes/memorias', RAM],
            ['componentes-y-partes/placas-madres', MOTHERBOARD],
            ['componentes-y-partes/procesadores', PROCESSOR],
            ['componentes-y-partes/tarjetas-graficas', VIDEO_CARD]
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
                url_webpage = 'https://comercialnet.cl/product' \
                              '-category/{}/page/{}/'.format(url_extension,
                                                             page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_container = soup.findAll('div', 'product-grid-item')

                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_container:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        if not soup.find('p', 'stock'):
            stock = -1
        elif soup.find('p', 'stock out-of-stock'):
            stock = 0
        else:
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        picture_urls = [tag['src'] for tag in soup.find('div', 'woocommerce-'
                                                               'product'
                                                               '-gallery')
                        .findAll('img')]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
