import json

import re
from datetime import datetime

from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Sams(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.sams.com.mx'

        category_paths = [
            ['electronica-y-computacion/computacion/memorias-y-discos-duros/'
             '_/N-8l0', 'ExternalStorageDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8,pt;q=0.7,pt-BR;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Host': 'www.sams.com.mx',
            'Pragma': 'no-cache',
            'Referer': 'https://www.sams.com.mx/electronica-y-computacion/c'
                       'omputacion/memorias-y-discos-duros/_/N-8l0',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/66.0.3359.181 Safari/'
                          '537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = '{}/sams/browse/{}'.format(base_url, category_path)
            print(category_url)

            response = session.get(category_url, verify=False).text
            json_data = json.loads(response)

            containers = json_data['mainArea']
            products_container = None

            for container in containers:
                if container['name'] == 'ResultsList':
                    products_container = container
                    break

            for container in products_container['contents'][0]['records']:
                attributes = container['attributes']
                product_url = base_url + attributes['product.seoURL'][0][1:-1]
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        product_id = re.search(r'/(\d+)$', url).groups()[0]

        session = session_with_proxy(extra_args)
        session.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8,pt;q=0.7,pt-BR;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Host': 'www.sams.com.mx',
            'Pragma': 'no-cache',
            'Referer': 'https://www.sams.com.mx/electronica-y-computacion/c'
                       'omputacion/memorias-y-discos-duros/_/N-8l0',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/66.0.3359.181 Safari/'
                          '537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }

        json_url = 'https://www.sams.com.mx/rest/model/atg/commerce/catalog/' \
                   'ProductCatalogActor/getSkuSummaryDetails?' \
                   'storeId=0000009999&skuId=' + product_id

        response = session.get(json_url, verify=False).text
        pricing_json = json.loads(response)

        price = Decimal(pricing_json['specialPrice'])

        products = []

        for sku_data in pricing_json['sku']['parentProducts']:
            sku = sku_data['id']
            picture_urls = ['https://www.sams.com.mx' +
                            sku_data['largeImageUrl']]
            description = html_to_markdown(sku_data['longDescription'])

            name = '{} {} {}'.format(sku_data['brand'],
                                     sku_data['displayName'],
                                     sku_data['shopTicketDesc'])

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
                'MXN',
                sku=sku,
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)

        return products
