import requests
from bs4 import BeautifulSoup

from .mercadolibre_chile import MercadolibreChile


class MercadolibreLg(MercadolibreChile):
    @classmethod
    def categories(cls):
        return [
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != 'Cell':
            return []

        session = requests.Session()
        product_urls = []

        category_url = 'https://tienda.mercadolibre.cl/lg'
        soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
        containers = soup.findAll('li', 'results-item')

        if not containers:
            raise Exception('Empty category: ' + category_url)

        for container in containers:
            product_url = container.find('a')['href']
            product_urls.append(product_url)

        return product_urls
