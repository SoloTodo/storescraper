import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class HpOnline(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Printer',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['notebooks', 'Notebook'],
            ['impresoras', 'Printer']
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.hponline.cl/c/{}?page={}' \
                               '&lazy=true'.format(category_path, page)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')
                product_cells = soup.findAll('div', 'catalogue-product')

                if not product_cells:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for cell in product_cells:
                    product_url = 'https://www.hponline.cl' + \
                                  cell.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text

        pricing_str = re.search(r'dataLayer = ([\S\s]+?);',
                                page_source).groups()[0]
        pricing_data = json.loads(pricing_str)[0]

        name = pricing_data['product_name']
        sku = pricing_data['sku_config']
        part_number = pricing_data['ean_code']
        price = Decimal(pricing_data['special_price'])

        soup = BeautifulSoup(page_source, 'html.parser')

        description = html_to_markdown(
            str(soup.find('div', 'product-description-container')))

        picture_urls = ['https:' + tag.find('img')['data-lazy'] for tag in
                        soup.findAll('div', {'id': 'image-product'})]

        availability_container = soup.find('meta',
                                           {'itemprop': 'availability'})

        if not availability_container:
            stock = 0
        elif soup.find('meta', {'itemprop': 'availability'})['href'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

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

        return [p]
