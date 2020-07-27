import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Siman(Store):
    country_url = ''
    currency_iso = ''
    category_filters = []

    @classmethod
    def categories(cls):
        return [
            'AirConditioner',
            'WashingMachine',
            'Refrigerator',
            'StereoSystem',
            'Television',
            'Stove',
            'Oven'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in cls.category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                url = 'https://{}.siman.com/{}?page={}'.format(
                    cls.country_url, category_path, page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                products = soup.findAll(
                    'section', 'vtex-product-summary-2-x-container')

                if not products:
                    if page == 1:
                        raise Exception('Empty url {}'.format(url))
                    else:
                        break

                for product in products:
                    product_url = 'https://{}.siman.com{}'.format(
                        cls.country_url, product.find('a')['href'])
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
