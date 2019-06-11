from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


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
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.amahogar.com.ar/{}'.format(
                category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.find('div', 'product_list').findAll(
                'div', 'product_list_item')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text.strip()
        key = soup.find('input', {'name': 'id_product'})['value'].strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()

        stock_container = soup.find('span', 'product-quantities')

        if stock_container:
            stock = int(stock_container['data-stock'])
        else:
            stock = -1

        description = html_to_markdown(str(soup.find('div', 'tab-content ')))

        price_string = soup.find('span', {'itemprop': 'price'})['content']
        normal_price = Decimal(remove_words(price_string))
        offer_price = normal_price

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'replace-2x')]

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
