import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, HEADPHONES, MOUSE, \
    KEYBOARD, CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class VirtualDrakon(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            CPU_COOLER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gabinetes', COMPUTER_CASE],
            ['headphones', HEADPHONES],
            ['mouses', MOUSE],
            ['teclados-mecanicos', KEYBOARD],
            ['ventiladores-rgb', CPU_COOLER]
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
                url_webpage = 'https://virtualdrakon.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product-item')
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
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_info = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        name = json_info['name']
        price = Decimal(json_info['offers'][0]['price'])
        if soup.find('form', 'variations_form'):
            products = []
            json_info = json.loads(soup.find('form', 'variations_form')[
                                       'data-product_variations'])
            for product in json_info:
                variant_name = name + ' - ' + product['attributes'][
                    'attribute_pa_color']
                sku = str(product['variation_id'])
                stock_container = BeautifulSoup(product['availability_html'],
                                                'html.parser').text.strip()
                stock = 0 if stock_container == 'Agotado' else int(
                    stock_container.split()[0])
                p = Product(
                    variant_name,
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
                    picture_urls=[product['image']['url']]
                )
                products.append(p)
            return products

        else:
            sku = str(json_info['sku'])
            if soup.find('p', 'stock in-stock'):
                stock = int(soup.find('p', 'stock in-stock').text.split()[0])
            elif json_info['offers'][0]['availability'] == \
                    'http://schema.org/InStock':
                stock = -1
            else:
                stock = 0

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
