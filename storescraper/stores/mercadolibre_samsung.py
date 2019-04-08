import requests
from bs4 import BeautifulSoup

from .mercadolibre_chile import MercadolibreChile


class MercadolibreSamsung(MercadolibreChile):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'VacuumCleaner',
            'WashingMachine',
            'AirConditioner',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_sections = [
            ('electrodomesticos/refrigeracion', 'Refrigerator'),
            ('electrodomesticos/pequenos', 'VacuumCleaner'),
            ('electrodomesticos/lavado-secado-ropa', 'WashingMachine'),
            ('electrodomesticos/climatizacion', 'AirConditioner'),
        ]

        session = requests.Session()
        product_urls = []

        for category_path, local_category in category_sections:
            if local_category != category:
                continue

            category_url = 'https://listado.mercadolibre.cl/{}/' \
                           '_Tienda_samsung'.format(category_path)
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.findAll('li', 'results-item')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls
