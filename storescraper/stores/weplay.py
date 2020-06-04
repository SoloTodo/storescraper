import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Weplay(Store):
    @classmethod
    def categories(cls):
        return [
            'VideoGameConsole',
            # 'Headphones',
            # 'Mouse',
            # 'Keyboard',
            # 'ExternalStorageDrive',
            # 'UsbFlashDrive',
            # 'MemoryCard',
            # 'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # ['consolas/consolas3ds.html', 'VideoGameConsole'],
            ['consolas/consolasswitch.html', 'VideoGameConsole'],
            # ['consolas/consolasps4.html', 'VideoGameConsole'],
            # ['consolas/consolasxboxone.html', 'VideoGameConsole'],
            ['computacion/audifonosgamer.html', 'Headphones'],
            ['computacion/teclados.html', 'Keyboard'],
            ['computacion/discosdurosexternos.html', 'ExternalStorageDrive'],
            ['computacion/mouse.html', 'Mouse'],
            ['computacion/pendrives.html', 'UsbFlashDrive'],
            ['computacion/tarjetasdememoria.html', 'MemoryCard'],
            ['computacion/parlantescomputacion.html', 'StereoSystem']
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_path, local_category = e

            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page > 20:
                    raise Exception('Page overflow: ' + category_path)

                url = 'https://www.weplay.cl/{}?p={}'.format(
                    category_path, page)

                response = session.get(url).text
                soup = BeautifulSoup(response, 'html.parser')

                products = soup.findAll('li', 'item')

                for product in products:
                    product_url = product.find('a')['href']

                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('div', 'product-name').find('h1').text.strip()
        sku = soup.find('p', 'sku').find('span').text.strip()

        web_stock = True

        if soup.find('p', 'out-of-stock'):
            web_stock = False

        store_stock = False
        stock_table = soup.find('table', 'stock-sucursal')

        for sucursal in stock_table.findAll('tr'):
            if sucursal.find('span', 'disponibleLimitado') or \
                    sucursal.find('span', 'disponibleCritico') or \
                    sucursal.find('span', 'disponible'):
                store_stock = True

        if store_stock or web_stock:
            stock = -1
        else:
            stock = 0

        price_container = soup.find('span', 'regular-price')

        if not price_container:
            if not web_stock:
                price_container = soup.find('p', 'old-price')
            else:
                price_container = soup.find('p', 'special-price')

        price = Decimal(
            price_container.find('span', 'price')
            .text.replace('$', '').replace('.', ''))

        picture_urls = [soup.find('p', 'product-image').find('img')['src']]
        description = html_to_markdown(
            str(soup.find('div', 'short-description')))

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
