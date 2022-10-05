from decimal import Decimal
import json

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class LadyLee(Store):

    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 0
            ready = False
            while not ready:
                if page > 10:
                    raise Exception('Page overflow')

                url_webpage = 'https://api.c8gqzlqont-mantenimi1-p1-public.m' \
                    'odel-t.cc.commerce.ondemand.com/occ/v2/myshop-spa/produ' \
                    'cts/search?query=LG&pageSize=100&currentPoS=D001&curren' \
                    'tPage={}'.format(page)

                data = session.get(url_webpage).text
                json_data = json.loads(data)['products']

                if len(json_data) == 0:
                    if page == 0:
                        raise Exception('Empty category: ' + url_webpage)
                    break

                for product in json_data:
                    if 'LG' not in product['name']:
                        ready = True
                        break
                    product_urls.append('https://ladylee.net' + product['url'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        sku = url.split('/')[4]
        product_url = 'https://api.c8gqzlqont-mantenimi1-p1-public.model-t.c' \
            'c.commerce.ondemand.com/occ/v2/myshop-spa/products/{}?fields=DE' \
            'FAULT,images(FULL,galleryIndex),ean&currentPoS=D001'.format(dsku)
        response = session.get(product_url, allow_redirects=False)

        json_data = json.loads(response.text)

        assert sku == json_data['code']

        description = json_data['description']
        name = json_data['name']
        price = Decimal(json_data['price']['value'])
        if json_data['availableForPickup']:
            stock = -1
        else:
            stock = 0

        picture_urls = [json_data['images'][0]['url']]

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
