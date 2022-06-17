import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class TokStock(Store):
    @classmethod
    def categories(cls):
        return [
            GAMING_CHAIR,
            NOTEBOOK,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['sillas', GAMING_CHAIR],
            ['tecnologia', NOTEBOOK]
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
                url_webpage = 'https://www.tokstock.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-small')

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
        name = soup.find('h1', 'product-title').text.strip()

        if soup.find('form', 'variations_form'):
            product_variations = json.loads(
                soup.find('form', 'variations_form')[
                    'data-product_variations'])
            products = []
            for variation in product_variations:
                variation_name = name + ' - ' + variation['attributes'][
                    'attribute_pa_color']
                key = str(variation['variation_id'])
                sku = variation['sku']
                price = Decimal(variation['display_price'])
                stock = variation['max_qty']
                if stock == "" and not variation['is_in_stock']:
                    stock = 0
                picture_urls = [variation['image']['src']]
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
            key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                -1]
            sku_tag = soup.find('span', 'sku')

            if sku_tag:
                sku = sku_tag.text.strip()
            else:
                sku = None

            if soup.find('p', 'price').find('ins'):
                price = Decimal(
                    remove_words(soup.find('p', 'price').find('ins').text))
            else:
                price = Decimal(
                    remove_words(soup.find('p', 'price').text))
            if soup.find('p', 'stock in-stock'):
                stock = int(soup.find('p', 'stock').text.split()[0])
            elif soup.find('p', 'stock out-of-stock'):
                stock = 0
            else:
                stock = -1
            picture_urls = [tag['src'] for tag in
                            soup.find('div', 'product-gallery').findAll('img')]
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
