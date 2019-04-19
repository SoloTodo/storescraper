from collections import defaultdict

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
    def discover_entries_for_category(cls, category, extra_args=None):
        if category != 'Cell':
            return []

        session = requests.Session()
        product_entries = defaultdict(lambda: [])

        category_url = 'https://tienda.mercadolibre.cl/lg'
        soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
        containers = soup.findAll('li', 'results-item')

        if not containers:
            raise Exception('Empty category: ' + category_url)

        for idx, container in enumerate(containers):
            product_url = container.find('a')['href']
            product_entries[product_url].append({
                'value': idx + 1,
                'section_name': 'Todos',
                'category_weight': 1
            })

        return product_entries
