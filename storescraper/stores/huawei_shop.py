import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, CELL, TABLET, WEARABLE, HEADPHONES
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
                if offset > 50:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://shop.huawei.com/cl/list-data-{}?sortField=registterTime&' \
                              'sortType=desc&prdAttrList=%5B%5D&pageNumber={}&pageSize=9'.format(url_extension, offset)

                data = session.get(url_webpage).text

                soup = BeautifulSoup(data, 'html.parser')
                product_container = soup.findAll('li', 'dataitem')

                if not product_container:
                    break
                for container in product_container:
                    product_url = container.find('a')['href']
                    product_urls.append('https:' + product_url.split('?')[0])
                offset += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        response_text = BeautifulSoup(response.text, 'html.parser').text
        product_info = re.search(r'var productInfo = transObjectAttribute\(.*?\)', response_text)
        inventory_info = re.findall(r'sbomInvInfo\["(.*?)"] = (.*?);', response_text)
        inventory = {i[0]: i[1] for i in inventory_info}
        json_info = json.loads(product_info.group(0)[40:-2])
        products = []
        products_json = json_info['sbomList']
        normal_price = Decimal(json_info['totalUnitPrice'])
        offer_price = normal_price
        for product in products_json:
            name = product['name'].replace('&#x2b;', ', ')
            sku = product['sbomCode']
            stock = int(inventory[sku])
            picture_urls = cls.create_pictures_urls(product)
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

    @classmethod
    def create_pictures_urls(cls, info):
        picture_urls = []
        base_url = 'https://img01.huaweifile.com/sg/ms/cl/pms/product/{}/group/428_428_{}'
        for picture in info['groupPhotoList']:
            picture_urls.append(base_url.format(info['gbomCode'], picture['photoName']))
        return picture_urls
