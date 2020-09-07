import json
import re
import math

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import \
    html_to_markdown, session_with_proxy, check_ean13


class BestBuyMexico(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
            'Ram',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Monitor',
            'Tablet',
            'Notebook',
            # 'Printer',
            'Cell',
            'Television',
            # 'AllInOne',
            'VideoGameConsole'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['1000067', 'SolidStateDrive'],
            ['1000069', 'Ram'],
            ['c1761', 'Mouse'],
            ['1001372', 'Monitor'],
            ['c51', 'Tablet'],
            ['c41', 'Notebook'],
            ['c45', 'Printer'],
            ['c53', 'Cell'],
            ['c35', 'Television'],
            ['c42', 'AllInOne'],
            ['1000071', 'VideoGameConsole'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                category_url = 'https://www.bestbuy.com.mx/c/api/listing?' \
                               'query=categoryId%24{}&page={}' \
                               ''.format(category_path, page)

                print(category_url)

                response = session.get(category_url)

                if response.status_code in [404, 500]:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                products_data = json.loads(response.text)
                product_cells = products_data['products']

                last_page = math.ceil(
                    products_data['totalCount']/products_data['pageSize'])

                if last_page == page:
                    done = True

                if not product_cells:
                    if page == 1:
                        raise Exception('No products found: {}'.format(
                            category_url))

                    break

                for product_cell in product_cells:
                    product_url = product_cell['seoPdpUrl']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text

        match = re.search(r'JSON.parse\("(.+)", reviver\);', page_source)
        product_data = json.loads(match.groups()[0].encode('utf-8').decode(
            'unicode_escape'))

        if 'customerPrice' not in product_data:
            return []

        name = product_data['title']
        sku = product_data['skuId']
        normal_price = Decimal(product_data['customerPrice'])
        offer_price = normal_price
        part_number = product_data.get('modelNumber')
        ean = product_data['upc']
        stock = -1
        condition = 'https://schema.org/NewCondition'

        if 'reacondicionado' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'

        if len(ean) == 12:
            ean = '0' + ean

        if not check_ean13(ean):
            ean = None

        soup = BeautifulSoup(page_source, 'html.parser')

        if not soup.find('div', 'shop-add-to-cart'):
            stock = 0
        elif 'Agotado' in soup.find('div', 'shop-add-to-cart').text:
            stock = 0
        elif 'Preventa' in soup.find('div', 'shop-add-to-cart').text:
            stock = 0

        description = html_to_markdown(
            str(soup.find('div', 'bbmx-product-description')))
        picture_urls = [tag['src'] for tag in
                        soup.findAll('img', {'data-track':
                                             'enlarge-image:image'})]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'MXN',
            sku=sku,
            condition=condition,
            part_number=part_number,
            ean=ean,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
