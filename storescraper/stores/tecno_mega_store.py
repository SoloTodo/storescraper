import json
import logging
from decimal import Decimal
from storescraper.categories import MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TecnoMegaStore(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            MONITOR
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + local_category)
                url_webpage = 'https://coretms.tecnomegastore.ec/admin/api/' \
                              'marcas/LG/ALL/{}/20/1/7'.format(page)
                print(url_webpage)
                response = session.get(url_webpage)
                json_container = json.loads(response.text)
                if not json_container['Products']:
                    if page == 1:
                        logging.warning('Empty category: ' + local_category)
                    break
                for container in json_container['Products']:
                    product_urls.append(
                        'https://www.tecnomegastore.ec/product/{}?code={}'
                        ''.format(container['URL'], container['sku']))
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        product_extension = url.split('?code=')[-1]
        response = session.get('https://coretms.tecnomegastore.ec/admin/'
                               'api/product/{}'.format(product_extension))
        json_product = json.loads(response.text)['Product'][0]
        part_number = json_product['numparte'] or None
        if part_number:
            name = part_number + ' - ' + json_product['description']
        else:
            name = json_product['description']
        sku = json_product['sku']
        stock = json_product['stock'][0]['S3']
        price = Decimal(str(json_product['priceW']))
        picture_urls = [json_product['image']]
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
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            part_number=part_number
        )
        return [p]
