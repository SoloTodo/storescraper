import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store


class Daewoo(Store):
    base_url = 'http://www.daewoo.cl/'

    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'WashingMachine',
            'Television',
            'AirConditioner',
            'Oven',
            'VacuumCleaner'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = requests.Session()

        product_urls = []
        full_catalog_paths = [
            ('refrigeradores/side-by-side/', 'Refrigerator'),
            ('lavadoras/carga-frontal/', 'WashingMachine'),
            ('televisores/led-tv/', 'Television'),
        ]

        for path, local_category in full_catalog_paths:
            if local_category != category:
                continue

            catalog_url = cls.base_url + path
            print(catalog_url)
            soup = BeautifulSoup(session.get(catalog_url).text, 'html.parser')
            for product_link in soup.findAll('a', 'link-modular'):
                product_urls.append(product_link['href'])

        electrodomesticos_categories = [
            ('Microondas', 'Oven'),
            ('Hornos', 'Oven'),
            ('Aspiradoras', 'VacuumCleaner'),
            ('Aire Acondicionado', 'AirConditioner'),
        ]

        soup = BeautifulSoup(
            session.get(cls.base_url + 'electrodomesticos/microondas/').text,
            'html.parser')

        for title, local_category in electrodomesticos_categories:
            if local_category != category:
                continue

            print(local_category)

            title_tag = soup.find(
                lambda tag: tag.name == 'h3' and tag.text == title)
            container = title_tag.parent
            for idx, product_link in enumerate(container.findAll('a')):
                article = container.findAll('article')[idx]
                try:
                    is_hidden = article['hidden']
                    continue
                except KeyError:
                    pass

                product_url = product_link['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')

        name = soup.find('div', 'detalle-producto').find('h4').text
        key = soup.find('div', 'detalle-producto').find('a', 'link-modular')[
            'href'].split('idp=')[1]
        picture_url = soup.find('span', {'id': 'zoom-product-0'}).find('img')[
            'src']

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            -1,
            Decimal(0),
            Decimal(0),
            'CLP',
            picture_urls=[picture_url]
        )

        return [p]
