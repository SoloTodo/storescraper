import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PROCESSOR, NOTEBOOK, HEADPHONES, MOUSE, \
    KEYBOARD, STORAGE_DRIVE, SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    RAM, MOTHERBOARD, VIDEO_CARD, MONITOR, CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


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
            VIDEO_CARD,
            MONITOR,
            CPU_COOLER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computadores-y-tablets/headsets', HEADPHONES],
            ['computadores-y-tablets/monitores-y-pantallas', MONITOR],
            ['computadores-y-tablets/mouses-y-teclados/mouse', MOUSE],
            ['computadores-y-tablets/mouses-y-teclados/categoria-1', KEYBOARD],
            ['computadores-y-tablets/notebook', NOTEBOOK],
            ['componentes-y-partes/almacenamiento/hdd', STORAGE_DRIVE],
            ['componentes-y-partes/almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['componentes-y-partes/fuentes-de-poder-psu/', POWER_SUPPLY],
            ['/componentes-y-partes/gabinetes', COMPUTER_CASE],
            ['componentes-y-partes/memorias', RAM],
            ['componentes-y-partes/placas-madres', MOTHERBOARD],
            ['componentes-y-partes/procesadores', PROCESSOR],
            ['componentes-y-partes/refrigeracion', CPU_COOLER],
            ['componentes-y-partes/tarjetas-graficas/'
             'tarjetas-graficas-nvidia', VIDEO_CARD],
            ['componentes-y-partes/tarjetas-graficas/'
             'tarjetas-graficas-amd', VIDEO_CARD],
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
                product_containers = soup.findAll('div', 'product-grid-item')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers:
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
        json_tag = soup.find('script', {'type': 'application/ld+json'})
        product_data = json.loads(json_tag.text)['@graph'][1]
        name = product_data['name']
        key = str(product_data['sku'])
        price = Decimal(product_data['offers'][0]['price'])
        description = html_to_markdown(product_data['description'])

        if product_data['offers'][0]['availability'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=key,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
