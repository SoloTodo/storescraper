import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class ChileGamerr(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['compra', MOTHERBOARD]
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
                url_webpage = 'https://www.chilegamerr.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', {
                    'data-hook': 'product-list-grid-item'})
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for i, container in enumerate(product_containers):
                    product_url = container.find('a')['href']
                    if len(product_containers) == len(product_urls):
                        return product_urls
                    if product_url in product_urls:
                        continue
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_container = json.loads(
            soup.find('script', {'id': 'wix-warmup-data'}).text)
        first_key = next(iter(product_container['appsWarmupData']))
        second_key = next(iter(next(iter(product_container['appsWarmupData'].
                                         values()))))
        product_id = \
            product_container['appsWarmupData'][first_key][second_key][
                'catalog'][
                'product']['id']
        name = soup.find('h1', {'data-hook': 'product-title'}).text
        sku = product_id
        stock = \
            product_container['appsWarmupData'][first_key][second_key][
                'catalog']['product']['inventory']['quantity']
        if stock == 500:
            stock = 0
        price = Decimal(remove_words(soup.find('span', {
            'data-hook': 'formatted-primary-price'}).text.split(',')[0]))
        picture_urls = ['https://static.wixstatic.com/media/' +
                        product_container['appsWarmupData'][first_key][
                            second_key]['catalog']['product']['media'][0][
                            'url']]
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
