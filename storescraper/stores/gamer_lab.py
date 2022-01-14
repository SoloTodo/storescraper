import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, KEYBOARD, HEADPHONES, GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GamerLab(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['mouse', MOUSE],
            ['teclados', KEYBOARD],
            ['audifonos', HEADPHONES],
            ['sillas-gamer', GAMING_CHAIR]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.gamerlab.cl/producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text

        if soup.find('form', 'variations_form cart'):
            variations = json.loads(soup.find('form', 'variations_form cart')[
                                        'data-product_variations'])
            products = []
            for variation in variations:
                variation_name = name + ' - ' + variation['attributes'][
                    'attribute_pa_switch']
                key = variation['sku']
                sku = str(variation['variation_id'])
                if variation['max_qty'] == '':
                    stock = 0
                else:
                    stock = variation['max_qty']
                price = Decimal(variation['display_price'])
                picture_urls = [variation['image']['url']]
                p = Product(
                    variation_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    key,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    picture_urls=picture_urls,

                )
                products.append(p)
            return products
        else:
            name = soup.find('h1', 'product_title').text
            key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                -1]
            sku = soup.find('span', 'sku').text.strip()
            if soup.find('button', {'name': 'add-to-cart'}):
                stock = -1
            else:
                stock = 0
            price_container = soup.find('p', 'price')
            if price_container.find('ins'):
                price = Decimal(remove_words(price_container.find('ins').text))
            else:
                price = Decimal(remove_words(price_container.text))
            picture_urls = [tag.find('a')['href'] for tag in
                            soup.find('div', {'id': 'product-images'}).findAll(
                                'figure')]
            p = Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,

            )
            return [p]
