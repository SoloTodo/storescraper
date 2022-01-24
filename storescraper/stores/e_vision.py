import json

from decimal import Decimal

from storescraper.categories import WASHING_MACHINE
from storescraper.store import Store
from storescraper.product import Product
from storescraper.utils import session_with_proxy


class EVision(Store):
    @classmethod
    def categories(cls):
        return [
            WASHING_MACHINE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            WASHING_MACHINE
        ]
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        product_urls = []

        for local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.evisionstore.com/api/product/' \
                          'onlineproducts-react.php'
            product_containers = json.loads(
                session.post(url_webpage).text)['online_products_all']

            if not product_containers:
                raise Exception('Empty')

            for container in product_containers:
                if container['brand'] != 'lg':
                    continue
                product_url = 'https://www.evisionstore.com/product/' + \
                              container['modelo']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        url_request = 'https://www.evisionstore.com/api/product/view-react.php'
        data = json.dumps({'model_number': url.split('product/')[1]})
        json_container = json.loads(session.post(url_request, data=data).text)
        name = json_container['product_view'][0]['product_name']
        sku = json_container['product_view'][0]['product_id']
        if json_container['product_view'][0]['allow_purchase'] == '0':
            stock = 0
        else:
            stock = -1

        price = Decimal(json_container['product_view'][0]['price']
                        .replace('$', '').replace(',', '').strip())

        picture_urls = [json_container['product_view'][0]['product_image']]

        description = json_container['product_view'][0][
            'short_description'].strip()

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
            description=description
        )

        return [p]
