import html
import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, MOUSE, NOTEBOOK, \
    STORAGE_DRIVE, TABLET, CELL, PRINTER, ALL_IN_ONE, TELEVISION, PROCESSOR, \
    CPU_COOLER, MOTHERBOARD, HEADPHONES, VIDEO_CARD, COMPUTER_CASE, RAM, \
    POWER_SUPPLY, SOLID_STATE_DRIVE, MEMORY_CARD, USB_FLASH_DRIVE, MONITOR, \
    VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class BookComputer(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            CELL,
            PRINTER,
            ALL_IN_ONE,
            TELEVISION,
            PROCESSOR,
            CPU_COOLER,
            MOTHERBOARD,
            HEADPHONES,
            VIDEO_CARD,
            COMPUTER_CASE,
            RAM,
            POWER_SUPPLY,
            SOLID_STATE_DRIVE,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            MONITOR,
            GAMING_CHAIR,
            STORAGE_DRIVE,
            VIDEO_GAME_CONSOLE,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['portatiles', NOTEBOOK],
            ['todo-en-uno', ALL_IN_ONE],
            ['accesorios-para-portatiles', VIDEO_CARD],
            ['monitores', MONITOR],
            ['monitores-proyectores', MONITOR],
            ['impresoras-y-escaneres', PRINTER],
            ['impresoras-multifuncionales', PRINTER],
            ['tabletas-digitales', TABLET],
            ['sillas', GAMING_CHAIR],
            ['televisores', TELEVISION],
            ['auriculares-y-manos-libres', HEADPHONES],
            ['gabinetes', COMPUTER_CASE],
            ['celulares', CELL],
            ['celulares-desbloqueados', CELL],
            ['memorias', RAM],
            ['ratones', MOUSE],
            ['notebook-outlet', NOTEBOOK],
            ['tablet-outlet', TABLET],
            ['outlet/impresoras', PRINTER],
            ['outlet/all-in-one', ALL_IN_ONE],
            ['outlet/monitores', MONITOR],
            ['outlet/televisores', TELEVISION],
            ['outlet/consolas', VIDEO_GAME_CONSOLE],
            ['gamers', HEADPHONES],
            ['notebook-y-desktop', NOTEBOOK],
            ['tarjetas-madre-placas-madre', MOTHERBOARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['chuwi', NOTEBOOK],
            ['thunderobot', NOTEBOOK],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 30:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.bookcomputer.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.bookcomputer.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        description = html_to_markdown(str(soup.find('div', 'description')))

        if soup.find('select', 'form-control'):
            products = []
            variations = json.loads(
                re.search(r"var productInfo = (.*);", response.text).groups()[
                    0])
            for product in variations:
                name = soup.find('h1', 'page-header').text

                if 'REACONDICIONADO' in name.upper():
                    condition = 'https://schema.org/RefurbishedCondition'
                else:
                    condition = 'https://schema.org/NewCondition'

                sku = str(product['variant']['id'])
                price = Decimal(product['variant']['price'])

                if 'PEDIDO' in name.upper():
                    stock = 0
                else:
                    stock = product['variant']['stock']

                picture_urls = [tag['src'] for tag in
                                soup.find('div', 'product-images').findAll(
                                    'img')]
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
                    condition=condition
                )
                products.append(p)
            return products
        else:
            json_info = json.loads(
                soup.find('script', {'type': 'application/ld+json'}).text,
                strict=False)
            if 'sku' not in json_info:
                sku = soup.find('form', 'product-form')['id'].split('-')[-1]
            else:
                sku = json_info['sku']
            name = sku + ' - ' + html.unescape(json_info['name'])

            if 'REACONDICIONADO' in name.upper():
                condition = 'https://schema.org/RefurbishedCondition'
            else:
                condition = 'https://schema.org/NewCondition'

            key = soup.find('form', 'product-form form-horizontal')[
                'action'].split('/')[-1]

            if 'PEDIDO' in name.upper():
                stock = 0
            else:
                stock = int(soup.find('input', {'id': 'input-qty'})['max'])

            price = Decimal(json_info['offers']['price'])
            picture_urls = []
            if 'image' in json_info:
                picture_urls = [json_info['image'].split('?')[0]]
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
                part_number=sku,
                picture_urls=picture_urls,
                description=description,
                condition=condition
            )
            return [p]
