import json
import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import MOTHERBOARD, RAM, PROCESSOR, VIDEO_CARD, \
    NOTEBOOK, TABLET, HEADPHONES, MOUSE, SOLID_STATE_DRIVE, KEYBOARD, \
    COMPUTER_CASE, MONITOR, STORAGE_DRIVE, POWER_SUPPLY, CPU_COOLER, CELL, \
    WEARABLE, STEREO_SYSTEM, GAMING_CHAIR, USB_FLASH_DRIVE, MEMORY_CARD


class InfographicsSolutions(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            RAM,
            PROCESSOR,
            VIDEO_CARD,
            NOTEBOOK,
            TABLET,
            HEADPHONES,
            MOUSE,
            SOLID_STATE_DRIVE,
            KEYBOARD,
            COMPUTER_CASE,
            MONITOR,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            CPU_COOLER,
            CELL,
            WEARABLE,
            STEREO_SYSTEM,
            GAMING_CHAIR,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['portatiles-notebook', NOTEBOOK],
            ['celulares-smarthphones', CELL],
            # ['tecnologia/tablet', TABLET],
            ['componentes-de-pc/placas-madres', MOTHERBOARD],
            ['componentes-de-pc/memorias-ram', RAM],
            ['componentes-de-pc/procesadores', PROCESSOR],
            ['componentes-de-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-de-pc/almacenamiento/discos-solidos',
             SOLID_STATE_DRIVE],
            ['componentes-de-pc/almacenamiento/discos-duros',
             STORAGE_DRIVE],
            ['componentes-de-pc/gabinetes', COMPUTER_CASE],
            ['pantallas-monitores', MONITOR],
            ['componentes-de-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-de-pc/refrigeracion', CPU_COOLER],
            ['accesorios/teclados', KEYBOARD],
            ['accesorios/audifonos-headset', HEADPHONES],
            ['accesorios/mouse', MOUSE],
            ['reloj-inteligente-smartwatch', WEARABLE],
            ['accesorios/parlantes', STEREO_SYSTEM],
            ['accesorios/sillas', GAMING_CHAIR],
            ['accesorios/pendrive', USB_FLASH_DRIVE],
            ['microsd', MEMORY_CARD],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                url = 'https://infographicssolutions.cl/categoria-producto/' \
                      '{}/page/{}/'.format(category_path, page)

                if page > 10:
                    raise Exception('Page overflow: ' + page)

                res = session.get(url)
                if res.status_code == 404:
                    if page == 1:
                        logging.warning('Invalid category: ' + url)
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                products = soup.findAll('div', 'product-grid-item')

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        product_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[1].text)[
            '@graph'][1]

        name = product_data['name']
        sku = str(product_data['sku'])
        key = soup.find('div', 'wd-wishlist-btn').find('a')['data-product-id']

        stock_container = soup.find('p', 'stock')

        if 'VENTA' in name.upper() and 'PRE' in name.upper():
            # Preventa
            stock = 0
        elif stock_container:
            stock_text = stock_container.text.split(' ')[0]
            if stock_text == 'Agotado':
                stock = 0
            else:
                stock = int(stock_text)
        else:
            stock = -1

        part_number_container = soup.find('span', 'sku')

        if part_number_container:
            part_number = part_number_container.text.strip()
        else:
            part_number = None

        offer_price = Decimal(product_data['offers'][0]['price'])
        normal_price = (offer_price * Decimal('1.05')).quantize(0)

        picture_containers = soup.findAll('div', 'product-image-wrap')
        picture_urls = [
            p.find('a')['href'] for p in picture_containers
            if validators.url(p.find('a')['href'])
        ]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number
        )

        return [p]
