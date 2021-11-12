import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MOUSE, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class WarenHouse(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MOUSE,
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos-gamer', HEADPHONES],
            ['mouse-gamer', MOUSE],
            ['teclados-gamer', KEYBOARD]
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
                url_webpage = 'https://warenhouse.cl/product-category/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('article', 'w-grid-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
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
        name = soup.find('h1', 'w-post-elm').text
        if soup.find('form', 'variations_form'):
            variations = json.loads(soup.find('form', 'variations_form')[
                                        'data-product_variations'])
            products = []
            for product in variations:
                if len(product['attributes']) > 1:
                    return []
                variation_name = name + ' - ' + product['attributes'][
                    'attribute_pa_color']
                sku = str(product['variation_id'])
                if product['is_in_stock']:
                    stock = product['max_qty']
                else:
                    stock = 0
                price = Decimal(product['display_price'])
                picture_urls = [product['image']['src']]
                p = Product(
                    variation_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    picture_urls=picture_urls
                )
                products.append(p)

        else:
            sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                -1]
            if soup.find('p', 'stock in-stock'):
                stock = int(soup.find('p', 'stock in-stock').text.split()[0])
            else:
                stock = 0
            price_container = soup.find('section', 'l-section wpb_row '
                                                   'product height_auto')
            if price_container.find('ins'):
                price = Decimal(remove_words(price_container.find('ins').
                                find('span', 'woocommerce-Price-amount').text))
            else:
                price = Decimal(remove_words(price_container.
                                find('span', 'woocommerce-Price-amount').text))

            picture_urls = [tag['src'] for tag in soup.find('div',
                            'woocommerce-product-gallery').findAll('img')]
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
                'CLP',
                sku=sku,
                picture_urls=picture_urls
            )
            return [p]
