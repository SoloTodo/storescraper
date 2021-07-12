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
            url_webpage = 'https://www.chilegamerr.cl/{}?page=100'.format(
                url_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('li', {
                'data-hook': 'product-list-grid-item'})

            for container in product_containers:
                tag_box = container.find('span', 'mxMP4')

                if tag_box and 'RESERVA' in tag_box.text.upper():
                    continue

                product_url = container.find('a')['href']
                product_urls.append(product_url)
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

        if 'RESERVA' in name.upper():
            stock = 0
        else:
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
