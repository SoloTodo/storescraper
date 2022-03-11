import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MONITOR, KEYBOARD, \
    COMPUTER_CASE, MOUSE, KEYBOARD_MOUSE_COMBO, GAMING_CHAIR, CPU_COOLER, \
    MOTHERBOARD, POWER_SUPPLY
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Nemz(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MONITOR,
            KEYBOARD,
            COMPUTER_CASE,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            GAMING_CHAIR,
            CPU_COOLER,
            MOTHERBOARD,
            POWER_SUPPLY,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['monitores', MONITOR],
            ['teclados', KEYBOARD],
            ['gabinetes', COMPUTER_CASE],
            ['mouse', MOUSE],
            ['combos-gamer', KEYBOARD_MOUSE_COMBO],
            ['sillas-gamer', GAMING_CHAIR],
            ['refrigeracion', CPU_COOLER],
            ['placas-madre', MOTHERBOARD],
            ['fuentes', POWER_SUPPLY],
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
                url_webpage = 'https://www.nemz.cl/product-category/{}/page' \
                              '/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty cagtegory: ' + url_extension)
                    break
                for container in product_containers.findAll('li'):
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
        if soup.find('form', 'variations_form'):
            products = []
            variations = json.loads(soup.find('form', 'variations_form')[
                                        'data-product_variations'])
            for variation in variations:
                variation_name = name
                for attr_name, attr_value in variation['attributes'].items():
                    variation_name += ' / ' + attr_name + ' ' + attr_value
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
                    sku,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    picture_urls=picture_urls
                )
                products.append(p)
            return products
        else:
            pn_container = soup.find('span', 'sku')

            if pn_container:
                name += ' ({})'.format(pn_container.text.strip())

            sku = soup.find('input', {'name': 'queried_id'})['value']
            description_tag = soup.find(
                'div', 'woocommerce-product-details__short-description')
            if description_tag and 'PREVENTA' in description_tag.text.upper():
                stock = 0
            elif soup.find('p', 'stock'):
                stock = 0
            elif soup.find('span', 'stock') and re.search(r'(\d+)', soup.find(
                    'span', 'stock').text):
                stock = int(
                    re.search(r'(\d+)', soup.find('span', 'stock').text)
                    .groups()[0])
            elif soup.find('span', 'stock') and '✅En Stock!':
                stock = -1
            else:
                return []
            price_container = soup.find('p', 'price')
            if price_container.find('ins'):
                price = Decimal(remove_words(price_container.find('ins').text
                                             .strip()))
            elif price_container.find('bdi'):
                price = Decimal(remove_words(price_container.find('bdi').text
                                             .strip()))
            else:
                return []
            picture_urls = [tag['src'] for tag in
                            soup.find('div', 'woocommerce-product-gallery')
                                .findAll('img')]
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
