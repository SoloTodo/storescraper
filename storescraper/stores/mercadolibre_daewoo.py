import requests
from bs4 import BeautifulSoup

from .mercadolibre_chile import MercadolibreChile


class MercadolibreDaewoo(MercadolibreChile):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            # 'WashingMachine'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('refrigeracion', 'Refrigerator'),
            ('lavado-y-secado-de-ropa', 'WashingMachine'),
        ]

        session = requests.Session()
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://electrodomesticos.mercadolibre.cl/{}/' \
                           '_Tienda_daewoo'.format(category_path)
            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            containers = soup.findAll('li', 'results-item')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls
