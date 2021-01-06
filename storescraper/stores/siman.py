import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Siman(Store):
    country_url = ''
    currency_iso = ''

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
            page = 1
            done = False
            while not done:
                if page > 30:
                    raise Exception('Page overflow')

                url_webpage = 'https://{}.siman.com/lg?page={}'.format(
                    cls.country_url, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                page_state_tag = soup.find('template',
                                           {'data-varname': '__STATE__'})
                page_state = json.loads(page_state_tag.text)

                done = True

                for key, product in page_state.items():
                    if 'productId' not in product:
                        continue
                    done = False
                    if product['brand'].upper() != 'LG':
                        continue
                    product_url = 'https://{}.siman.com/{}/p'.format(
                        cls.country_url, product['linkText'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)

        if product_data['brand'] != 'LG':
            return []

        name = product_data['name']
        sku = soup.find(
            'meta', {'property': 'product:retailer_item_id'})['content']
        stock = 0
        if soup.find('meta', {'property': 'product:availability'})['content'] \
                == 'instock':
            stock = -1

        price = Decimal(product_data['offers']['lowPrice'])
        picture_urls = [product_data['image']]
        description = product_data['description']

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
            cls.currency_iso,
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
