import demjson
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Enel(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'AirConditioner',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['299-tradicionales', 'Lamp'],
            ['300-smart', 'Lamp'],
            ['301-decorativas', 'Lamp'],
            ['105-split-sin-instalacion', 'AirConditioner'],
            ['216-aire-acondicionados-portatiles', 'AirConditioner'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.tiendaenel.cl/' + category_path
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            product_containers = soup.findAll('section', 'cs-product')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')
        name = soup.find('h1').text.strip()

        sku = soup.find('input', {'name': 'id_product'})['value'].strip()

        price = Decimal(soup.find(
            'meta', {'property': 'product:price:amount'})['content'])
        price = price.quantize(0)

        stock = int(re.search(r'quantityAvailable = (\d+?);',
                              page_source).groups()[0])

        description = html_to_markdown(str(soup.find('div', 'product-tab')))

        picture_tags = soup.findAll('img', {'itemprop': 'image'})[1:]
        picture_urls = []

        for tag in picture_tags:
            picture_url = demjson.decode(
                re.search(r'rel="(.+?)"',
                          str(tag.parent)).groups()[0])['largeimage']
            picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
