import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class MacOnline(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Tablet'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        discovered_urls = []

        category_paths = [
            ['mac', 'Notebook'],
            ['ipad', 'Tablet'],
            ['iphone', 'Cell'],
        ]

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            category_url = 'https://maconline.com/t/{}'.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            subcategories = soup.find('ul', 'list-unstyled').findAll('li')

            for subcategory in subcategories:
                subcategory_url = 'https://maconline.com{}'.format(
                    subcategory.find('a')['href'].split('?')[0]
                )
                discovered_urls.append(subcategory_url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if not response.ok:
            return []

        page_source = response.text

        soup = BeautifulSoup(page_source, 'html.parser')

        default_picture_url = soup.find('img', {'itemprop': 'image'})['src']

        json_data = re.search(r'options: (.*)', page_source)

        json_data = json.loads(json_data.groups()[0][:-1])

        json_products = cls.__extract_products(json_data)

        for json_product in json_products.values():
            name = json_product['name']
            part_number = json_product['sku']
            sku = str(json_product['id'])
            description = html_to_markdown(json_product['technical_details'])
            description += '\n\n' + html_to_markdown(
                json_product['description'])

            stock = sum(json.loads(json_product['stock_locations']).values())

            price = Decimal(remove_words(json_product['price']))

            picture_tag = soup.find('li', 'tmb-' + sku)
            if picture_tag:
                picture_urls = [picture_tag.find('a')['href']]
            else:
                picture_urls = [default_picture_url]

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
                part_number=part_number,
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)

        return products

    @classmethod
    def __extract_products(cls, prods):
        if not prods:
            return {}

        if 'id' in prods:
            return {
                prods['id']: prods
            }

        result = {}
        for value in prods.values():
            result.update(cls.__extract_products(value))

        return result
