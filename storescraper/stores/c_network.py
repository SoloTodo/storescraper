import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class CNetwork(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Monitor'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['hdd', 'StorageDrive'],
            ['ssd', 'SolidStateDrive'],
            ['tarjeta-madre', 'Motherboard'],
            ['procesadores', 'Processor'],
            ['memoria-ram', 'Ram'],
            ['xn--tarjeta-de-vdeo-t9a', 'VideoCard'],
            ['fuente-de-poder', 'PowerSupply'],
            ['gabinete', 'ComputerCase'],
            ['mouse', 'Mouse'],
            ['teclado', 'Keyboard'],
            ['xn--kit-teclado-mouse--combo-perifricos-cic',
             'KeyboardMouseCombo'],
            ['monitores', 'Monitor']
        ]

        base_url = 'https://aaccd439-730d-4520-b08e-0e33f14eba20' \
                   '.mysimplestore.com/api/v2/products?' \
                   'taxon_permalink={}&page={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                response = session.get(url)
                products_data = json.loads(response.text)['products']

                if not products_data:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                for product in products_data:
                    product_url = 'http://cnetwork.mx{}'.format(
                        product['relative_url'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        api_extension = url.split('?')[1].split('=')[1].replace('%2F', '/')
        api_url = 'https://aaccd439-730d-4520-b08e-0e33f14eba20.' \
                  'mysimplestore.com/api/v2/{}?' \
                  'app=vnext&timestamp=1584377824950'.format(api_extension)

        page_source = session.get(api_url).text
        product_data = json.loads(page_source)

        name = product_data['name']
        sku = product_data['sku']

        if product_data['in_stock']:
            stock = -1
        else:
            stock = 0

        price = Decimal(product_data['price'])
        picture_urls = [p['large_url'] for p in product_data['assets']]
        description = html_to_markdown(product_data['description'])

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
            'MXN',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
