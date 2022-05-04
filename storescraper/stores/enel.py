import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import AIR_CONDITIONER, SPACE_HEATER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Enel(Store):
    @classmethod
    def categories(cls):
        return [
            AIR_CONDITIONER,
            SPACE_HEATER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['aire-acondicionado.list.html',
             AIR_CONDITIONER],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.enelxstore.com/content/enel-x-store/' \
                           'cl/es/e-shop/{}'.format(category_path)
            print(category_url)
            products_data = json.loads(session.get(category_url).text)

            for product_entry in products_data:
                product_url = 'https://www.enelxstore.com' + \
                              product_entry['path']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')
        name = soup.find('h1', 'name').text.strip()
        key = soup.find('input', {'id': 'engineCode'})['value']
        price = Decimal(soup.find('span', {'itemprop': 'price'})['data-price'])

        picture_urls = []

        for picture_tag in soup.findAll('div', 'photo--active'):
            picture_path = picture_tag['data-image'].split('.resize')[0]
            picture_url = 'https://www.enelxstore.com/' + picture_path
            picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            -1,
            price,
            price,
            'CLP',
            picture_urls=picture_urls
        )

        return [p]
