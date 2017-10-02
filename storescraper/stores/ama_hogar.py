import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown


class AmaHogar(Store):
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
            ['1521-heladeras-con-freezer', 'Refrigerator'],
            ['1523-heladeras-con-congelador', 'Refrigerator'],
            ['1481-freezer', 'Refrigerator'],
            ['1470-split', 'AirConditioner'],
            ['1487-calefones', 'WaterHeater'],
            ['1492-lavarropas', 'WashingMachine'],
            ['1491-secarropas', 'WashingMachine'],
            ['1483-cocinas', 'Stove'],
            ['1475-anafes', 'Stove'],
        ]

        product_urls = []
        session = requests.Session()

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.amahogar.com.ar/{}'.format(
                category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.find('div', {'id': 'product_list'}).findAll(
                'div', 'product_block')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = requests.Session()
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text.strip()
        key = soup.find('input', {'name': 'id_product'})['value'].strip()
        sku = soup.find('span', 'editable').text.strip()
        stock = int(soup.find('span', {'id': 'quantityAvailable'}).text)
        description = html_to_markdown(str(soup.find('div', {'id': 'idTab1'})))

        price_string = soup.find('span', {'id': 'our_price_display'}).text

        normal_price = Decimal(remove_words(price_string))
        offer_price = normal_price

        picture_urls = None

        pictures_container = soup.find('ul', {'id': 'thumbs_list_frame'})
        if pictures_container:
            picture_urls = []
            for link in pictures_container.findAll('a'):
                picture_urls.append(link['href'])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
