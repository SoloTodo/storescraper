from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Olier(Store):
    base_url = 'https://www.lg.com'
    country_code = 'cl'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'Stove',
            'WashingMachine',
            'AirConditioner'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['tv-c148', 'Television'],
            ['reproductores-portatiles-c140', 'StereoSystem'],
            ['equipo-de-sonido-c138', 'StereoSystem'],
            ['celulares-c142', 'Cell'],
            ['heladeras-c42', 'Refrigerator'],
            ['freezer-c40', 'Refrigerator'],
            ['horno-electrico-c16', 'Oven'],
            ['microondas-c20', 'Oven'],
            ['encimeras-c13', 'Stove'],
            ['cocinas-c12', 'Stove'],
            ['lavarropas-c18', 'WashingMachine'],
            ['secarropas-c22', 'WashingMachine'],
            ['aire-split-c28', 'AirConditioner'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        base_url = 'https://www.olier.com.py/catalogo/{}.{}'

        for c in category_paths:
            category_path, local_category = c

            if category != local_category:
                continue

            page = 1

            while True:
                url = base_url.format(category_path, page)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                print(url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('div', 'product')

                if not product_containers:
                    break

                for product in product_containers:
                    product_url = 'https://olier.com.py/{}'.format(
                        product.find('a')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()
        sku = soup.find('span', 'sku').text.strip()
        stock = -1

        price = Decimal(
            soup.find('p', 'price').find('span', 'amount')
                .text.replace('₲.', '').replace('.', ''))

        picture_urls = [soup.find('meta', {'name': 'og:image'})['content']]

        return [Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'PYG',
            sku=sku,
            picture_urls=picture_urls
        )]
