import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, html_to_markdown


class Huawei(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Cell',
            'Tablet',
            'Wereable'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Notebooks
            ['403', 'Notebook'],
            # Cells
            ['387', 'Cell'],
            # Tablets
            ['407', 'Tablet'],
            # Wereables
            ['399', 'Wereable'],
            # Headphones
            ['391', 'Headphone']
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            offset = 1
            while True:
                url_webpage = 'https://shop.huawei.com/cl/list-data-{}?sortField=registterTime&' \
                              'sortType=desc&prdAttrList=%5B%5D&pageNumber={}&pageSize=9'.format(url_extension, offset)

                data = session.get(url_webpage).text

                soup = BeautifulSoup(data, 'html5lib')
                product_container = soup.findAll('li', 'dataitem')

                if not product_container:
                    break
                for container in product_container:
                    product_url = container.find('a')['href']
                    # TODO add https: to begin of href
                    product_urls.append(product_url)
                offset += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        if response.status_code == 500:
            return []
        soup = BeautifulSoup(response.text, 'html5lib')
        script_container = soup.findAll('script')
        json_info, inventory = cls.get_products_info(script_container)
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
    def get_products_info(cls, script_container):
        for s in script_container:
            product_info = re.search(r'var productInfo = transObjectAttribute\(.*?\)', s.text)
            inventory_info = re.findall(r'sbomInvInfo\["(.*?)"] = (.*?);', s.text)
            if product_info and inventory_info:
                break
        inventory = {i[0]: i[1] for i in inventory_info}

        json_info = json.loads(product_info.group(0)[40:-2])
        return json_info, inventory

    @classmethod
    def create_pictures_urls(cls, info):
        picture_urls = []

        base_url = 'https://img01.huaweifile.com/sg/ms/cl/pms/product/{}/{}'
        for picture in info['groupPhotoList']:
            picture_urls.append(base_url.format(info['gbomCode'], picture['photoName']))
        return picture_urls
