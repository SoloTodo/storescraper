import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, TABLET, HEADPHONES, TELEVISION, \
    MONITOR, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class MiStore(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            TABLET,
            HEADPHONES,
            TELEVISION,
            MONITOR,
            WEARABLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extension = [
            ['smartphones', CELL],
            ['ecosystem/computacion/tablets', TABLET],
            ['ecosystem/audio/audifonos', HEADPHONES],
            ['ecosystem/video/mi-tv', TELEVISION],
            ['monitores', MONITOR],
            ['ecosystem/smartwatch-bands', WEARABLE]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extension:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://mistorechile.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-small')

                if not product_containers:
                    if page == 1:
                        logging.warning('Emtpy category: ' + url_extension)
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
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text.strip()
        if soup.find('form', 'variations_form'):
            variations_container = json.loads(
                soup.find('form', 'variations_form')[
                    'data-product_variations'])
            products = []
            for variation in variations_container:
                variation_name = name + ' - ' + variation['attributes'][
                    'attribute_pa_color']
                sku = str(variation['variation_id'])
                part_number = variation['sku']
                stock = 0 if variation['max_qty'] == '' else variation[
                    'max_qty']
                price = Decimal(variation['display_price'])
                picture_urls = [variation['image']['src']]
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
                    sku=part_number,
                    part_number=part_number,
                    picture_urls=picture_urls,
                )
                products.append(p)
            return products
        else:
            sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                -1]
            part_number = soup.find('span', 'sku').text
            if soup.find('p', 'stock in-stock'):
                stock_container = soup.find('p', 'stock in-stock').find(
                    'tbody').findAll('tr')[1].findAll('td')[1].text.strip()
                if stock_container == '50+':
                    stock = 50
                else:
                    stock = int(stock_container)

            else:
                stock = 0
            price_container = soup.find('p', 'price')
            if price_container.find('ins'):
                price = Decimal(remove_words(price_container.find('ins').text))
            else:
                price = Decimal(remove_words(price_container.find('bdi').text))
            picture_container = soup.find('div', 'product-gallery')
            if picture_container.find('div', 'product-thumbnails'):
                picture_urls = [tag['src'] for tag in
                                picture_container.find('div',
                                'product-thumbnails').findAll('img')]
            else:
                picture_urls = [tag['src'] for tag in
                                picture_container.findAll('img')]

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
                sku=part_number,
                part_number=part_number,
                picture_urls=picture_urls,
            )
            return [p]
