import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import NOTEBOOK, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PortatilChile(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            VIDEO_GAME_CONSOLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['4-notebooks', NOTEBOOK],
            ['42-especial-2-1', NOTEBOOK],
            ['71-consolas', VIDEO_GAME_CONSOLE],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 15:
                    raise Exception('page overflow')
                url_webpage = 'https://portatilchile.com/{}?page={}' \
                              ''.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('article',
                                                  'product-miniature')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category')
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
        json_data = json.loads(
            soup.find('div', {'id': 'product-details'})['data-product'])

        sku = str(json_data['id_product'])
        part_number = json_data['reference'] or None
        name = json_data['name']
        price = Decimal(json_data['price_amount'])

        stock_container = soup.find('div', 'product-quantities')
        if stock_container:
            stock = int(stock_container.find('span')['data-stock'])
        else:
            stock = 0
        if soup.find('div', {'id': 'product-images-thumbs'}):
            picture_urls = [tag['data-image-large-src'] for tag in
                            soup.find('div',
                                      {'id': 'product-images-thumbs'}).findAll(
                                'img')]
        else:
            picture_urls = [
                soup.find('div', 'images-container').find('img')[
                    'data-image-large-src']]

        condition = 'https://schema.org/NewCondition'
        for f in json_data['features']:
            if f['name'] == 'Garantia':
                if 'Open Box' in f['value']:
                    condition = 'https://schema.org/RefurbishedCondition'

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
            part_number=part_number,
            picture_urls=picture_urls,
            condition=condition
        )

        return [p]
