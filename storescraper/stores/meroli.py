from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class \
        Meroli(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['Heladeras/9', 'Refrigerator'],
            ['Freezer/76', 'Refrigerator'],
            ['Aire-Acondicionado/17', 'AirConditioner'],
            ['Calefones/24', 'WaterHeater'],
            ['Lavarropas/11', 'WashingMachine'],
            # ['Lavasecarropas/25', 'WashingMachine'],
            # ['Secarropas-por-Calor/31', 'WashingMachine'],
            ['Secarropas-Centrifugo/34', 'WashingMachine'],
            ['Cocinas/12', 'Stove'],
            ['Anafes/23', 'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.meroli.com/lista/productos/{}'.format(
                    category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.findAll('div', 'one-product')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = 'https://www.meroli.com' + \
                              container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('meta', {'name': 'Title'})['content'].strip()
        sku = soup.find('input', {'name': 'id'})['value'].strip()

        price_string = soup.find('input', {'id': 'product_price'})['value']
        price = Decimal(price_string)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'especificaciones-container'})))

        picture_urls = [tag['data-zoom-image'] for tag in
                        soup.find('div', 'owl-carousel').findAll('img')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
