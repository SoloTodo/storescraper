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


class Todoclick(Store):
    @classmethod
    def categories(cls):
        return [
            'AllInOne',
            'Notebook',
            'StorageDrive',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'PowerSupply',
            'ComputerCase',
            'Motherboard',
            'Processor',
            'VideoCard',
            'Ram',
            'Tablet',
            'Headphones',
            'Mouse',
            'Keyboard',
            'Monitor',
            'Printer',
            'UsbFlashDrive',
            'StereoSystem',
            'Wearable',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['notebooks', 'Notebook'],
            ['all-in-one', 'AllInOne'],
            ['disco-duro', 'StorageDrive'],
            ['fuentes-de-poder', 'PowerSupply'],
            ['gabinetes', 'ComputerCase'],
            ['placa-madre', 'Motherboard'],
            ['procesadores', 'Processor'],
            ['tarjetas-de-video', 'VideoCard'],
            ['memoria-ram', 'Ram'],
            ['tablet', 'Tablet'],
            ['audifonos', 'Headphones'],
            ['audifonos-gamer', 'Headphones'],
            ['mouse-accesorios', 'Mouse'],
            ['mouse-gamer', 'Mouse'],
            ['teclados', 'Keyboard'],
            ['teclado-gamer', 'Keyboard'],
            ['monitores', 'Monitor'],
            ['impresoras-laser-impresoras', 'Printer'],
            ['impresoras-ink-jet-impresoras', 'Printer'],
            ['multifuncional-laser', 'Printer'],
            ['multifuncional-ink-jet', 'Printer'],
            ['pendrive', 'UsbFlashDrive'],
            ['parlantes', 'StereoSystem'],
            ['soundbar', 'StereoSystem'],
            ['smartwatch', 'Wearable']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 15:
                    raise Exception('Page overflow')

                if page == 1:
                    page_url = 'https://www.todoclick.cl/categoria/{}/'.format(
                        category_path)
                else:
                    page_url = 'https://www.todoclick.cl/categoria/{}/page/' \
                               '{}/'.format(category_path, page)

                print(page_url)
                response = session.get(page_url)

                if response.url != page_url:
                    raise Exception('Mismatch: ' + response.url + ' ' +
                                    page_url)

                soup = BeautifulSoup(response.text, 'html.parser')
                products = soup.findAll('li', 'product')

                if not products:
                    break

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')

        name = soup.find('h1', 'product_title').text
        sku = soup.find('div', 'ct-code-block').text.split(':')[1].strip()

        stock = 0
        stock_container = soup.find('p', 'stock in-stock')
        if stock_container:
            stock = int(stock_container.text.split(' ')[0])

        offer_price_container = soup.find('p', 'price')

        if offer_price_container.find('ins'):
            offer_price_container = offer_price_container.find('ins')

        offer_price = Decimal(offer_price_container.find('span', 'amount')
                              .text.replace('$', '').replace('.', ''))
        normal_price = Decimal(soup.find('div', {'id': 'Webpay'})
                               .text.split('$')[1].replace('.', ''))

        images = soup.findAll('img', 'wp-post-image')
        picture_urls = [i['src'] for i in images]

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
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
