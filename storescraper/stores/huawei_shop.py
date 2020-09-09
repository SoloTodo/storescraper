import html
import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, CELL, TABLET, \
    WEARABLE, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class HuaweiShop(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            CELL,
            TABLET,
            WEARABLE,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Notebooks
            ['403', NOTEBOOK],
            # Cells
            ['387', CELL],
            # Tablets
            ['407', TABLET],
            # Wearables
            ['399', WEARABLE],
            # Headphones
            ['391', HEADPHONES]
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            offset = 1
            while True:
                if offset > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://shop.huawei.com/cl/list-data-{}' \
                              '?pageNumber={}&pageSize=9'. \
                    format(url_extension, offset)

                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'dataitem')

                if not product_containers:
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https:' + product_url.split('?')[0])
                offset += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        response_text = BeautifulSoup(response.text, 'html.parser').text
        product_info = re.search(
            r"var productInfo = transObjectAttribute\('(.*?)'\)",
            response_text
        )
        stock_info = re.findall(r'sbomInvInfo\["(.*?)"] = (.*?);',
                                response_text)
        stock_info = {i[0]: i[1] for i in stock_info}
        json_info = json.loads(product_info.groups()[0])
        products = []
        products_json = json_info['sbomList']
        normal_price = Decimal(json_info['totalUnitPrice'])
        offer_price = normal_price
        picture_base_url = 'https://img01.huaweifile.com/sg/ms' \
                           '/cl/pms/product/{}/group/428_428_{}'
        for product in products_json:
            name = html.unescape(product['name'])
            sku = product['sbomCode']
            stock = int(stock_info[sku])
            picture_urls = [picture_base_url.format(product['gbomCode'],
                                                    picture['photoName'])
                            for picture in product['groupPhotoList']]
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
                'CLP',
                sku=sku,
                picture_urls=picture_urls

            )
            products.append(p)

        return products
