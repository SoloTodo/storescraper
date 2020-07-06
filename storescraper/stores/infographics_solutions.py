import json
import re

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, \
    session_with_proxy


class InfographicsSolutions(Store):
    @classmethod
    def categories(cls):
        return [
            'Motherboard',
            'Ram',
            'Processor',
            'VideoCard',
            'Notebook',
            'Tablet',
            'Headphones',
            'Mouse',
            'SolidStateDrive',
            'StorageDrive',
            'Keyboard',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['componentes-de-pc/placa-madre/', 'Motherboard'],
            ['componentes-de-pc/memorias-ram/', 'Ram'],
            ['componentes-de-pc/procesadores/', 'Processor'],
            ['componentes-de-pc/tarjetas-de-video/', 'VideoCard'],
            ['equipos/portatiles/', 'Notebook'],
            ['tecnologia/tablet/', 'Tablet'],
            ['accesorios-gamer/headset-audifonos/', 'Headphones'],
            ['accesorios-gamer/mouse/', 'Mouse'],
            ['componentes-de-pc/almacenamiento/discos-solidos/',
             'SolidStateDrive'],
            ['componentes-de-pc/almacenamiento/discos-duros/',
             'StorageDrive'],
            ['accesorios-gamer/teclados/',
             'Keyboard'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = 'https://infograsolutions.cl/categoria-producto/{}'\
                .format(category_path)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            products = soup.findAll('div', 'product-grid-item')

            for product in products:
                product_urls.append(product.find('a')['href'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'product_title').text
        sku = soup.find('div', 'wd-wishlist-btn').find('a')['data-product-id']

        stock_container = soup.find('p', 'stock')

        if stock_container:
            stock_text = stock_container.text.split(' ')[0]
            if stock_text == 'Agotado':
                stock = 0
            else:
                stock = int(stock_text)
        else:
            stock = -1

        price_container = soup.find('p', 'price')

        if price_container.find('ins'):
            price = Decimal(price_container.find('ins').text.replace(
                '$', '').replace('.', ''))
        else:
            price = Decimal(price_container.text.replace(
                '$', '').replace('.', ''))

        picture_containers = soup.findAll('div', 'product-image-wrap')
        picture_urls = [p.find('a')['href'] for p in picture_containers]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

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
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
