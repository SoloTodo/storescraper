from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Rodo(Store):
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
            ['hogar.html?cat=34', 'Refrigerator'],
            ['hogar/agua-caliente/calefones.html?cat=', 'WaterHeater'],
            ['climatizacion/aire-acondicionado/split.html?cat=',
             'AirConditioner'],
            ['hogar/lavado-y-secado/lavarropas.html?cat=',
             'WashingMachine'],
            ['hogar/cocina.html?cat=73', 'Stove'],
            ['hogar.html?cat=74', 'Stove'],
            ['hogar/cocina.html?cat=77', 'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False

            while True:
                category_url = 'http://www.rodo.com.ar/{}&limit=30&p={}' \
                               ''.format(category_path, page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')
                containers = soup.findAll('div', 'product-box')

                if not containers:
                    raise Exception('Empty category: ' + category_url)

                for container in containers:
                    product_url = container.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break
                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'product-name').text.strip()
        sku = soup.find('input', {'name': 'product'})['value'].strip()

        price_string = soup.find('span', 'price').text

        price = Decimal(price_string.replace(
            '.', '').replace('$', '').replace(',', '.'))

        description = html_to_markdown(
            str(soup.find('div', 'product-collateral')))

        picture_urls = [tag['src'] for tag in
                        soup.findAll('img', {'id': 'image'})]

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
