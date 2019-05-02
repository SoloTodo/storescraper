from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy

import re
import json


class Tomalo(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Tablet',
            'StereoSystem',
            'CellAccesory',
            'Headphones',
            'Wearable',
            'MemoryCard'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('dispositivos-moviles', 'Cell'),
            # ('galaxy-s10', 'Cell'),
            # ('119-promo-s8-s9-s9', 'Cell'),
            # ('91-galaxy-note-9', 'Cell'),
            # ('116-promo-level-u', 'Cell'),
            ('tablet', 'Tablet'),
            ('books', 'Tablet'),
            # ('95-parlantes-jbl', 'StereoSystem'),
            ('carcasas', 'CellAccesory'),
            ('hogar-inteligente', 'CellAccesory'),
            ('audifonos', 'Headphones'),
            ('wearables', 'Wearable'),
            # ('96-tarjeta-memoria-micro-sd', 'MemoryCard')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False

            while True:
                if page > 10:
                    raise Exception('Page overflow')

                url = 'https://www.tomalo.cl/{}?p={}'\
                    .format(category_path, page)
                print(url)
                response = session.get(url)

                if response.status_code == 404:
                    raise Exception('Emtpy category: ' + url)

                soup = BeautifulSoup(response.text, 'html.parser')

                for container in soup.findAll('div', 'product_container'):
                    product_url = container\
                        .find('a', 'product_img_link')['href']

                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)

        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        products = []

        name = soup.find('h1', {'itemprop': 'name'}).text
        available = soup.find('link', {'itemprop': 'availability'})
        stock = -1 if available else 0
        price = Decimal(
            soup.find('span', {'id': 'our_price_display'})['content'])

        picture_urls = []
        pictures = soup.find('div', {'id': 'thumbs__list'}).findAll('li')

        for picture in pictures:
            picture_urls.append(picture.find('img')['src']
                                .replace('cart_default', 'thickbox_default'))

        variant_container = soup.find('ul', {'id': 'color_to_pick_list'})

        if variant_container:
            variants = variant_container.findAll('li')

            for variant in variants:
                js_data = re.search('var combinations = (.+?);', data).group(1)
                json_data = json.loads(js_data)

                color_code = variant.find('a')['id'].replace('color_', '')
                color_name = variant.find('a')['title']
                model_url = '{}#/{}-selecciona_tu_color-{}'\
                    .format(url, color_code, color_name)
                for d in json_data:
                    if color_name == json_data[d]['attributes_values']['3']:
                        key = '{}-{}'\
                            .format(json_data[d]['reference'], color_name)
                        break

                products.append(
                    Product(
                        '{} ({})'.format(name, key),
                        cls.__name__,
                        category,
                        model_url,
                        url,
                        key,
                        stock,
                        price,
                        price,
                        'CLP',
                        sku=key,
                        part_number=key,
                        picture_urls=picture_urls
                    )
                )
        else:
            key = re.search("'sku': '(.+?)',", data).group(1)
            products.append(
                Product(
                    '{} ({})'.format(name, key),
                    cls.__name__,
                    category,
                    url,
                    url,
                    key,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=key,
                    part_number=key,
                    picture_urls=picture_urls
                )
            )

        return products
