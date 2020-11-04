import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import AIR_CONDITIONER, STOVE, CELL_ACCESORY, \
    OVEN, WASHING_MACHINE, REFRIGERATOR, STEREO_SYSTEM, OPTICAL_DISK_PLAYER, \
    TELEVISION


class PlazaLama(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only interested in LG products
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != TELEVISION:
            return []

        page = 1

        while True:
            if page >= 10:
                raise Exception('Page overflow')

            url = 'https://plazalama.com.do/search?q=LG&type=product&page=' \
                  '{}'.format(page)
            print(url)

            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.findAll('div', 'search-result')

            if not items:
                if page == 1:
                    logging.warning('Empty category:' + url)
                break

            for item in items:
                path = item.find('a')['href'].split('?')[0]
                product_urls.append(
                    'https://plazalama.com.do' + path)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        products_data = json.loads(re.search(r'var boldTempProduct =(.+);',
                                             response.text).groups()[0])
        description = html_to_markdown(products_data['description'])
        picture_urls = ['https:' + x for x in products_data['images']]
        products = []

        for variant in products_data['variants']:
            key = str(variant['id'])
            sku = variant['sku']
            name = variant['name']

            if variant['available']:
                stock = -1
            else:
                stock = 0

            price = Decimal(variant['price']) / Decimal(100)

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                price,
                price,
                'DOP',
                sku=sku,
                picture_urls=picture_urls,
                description=description
            ))

        return products
