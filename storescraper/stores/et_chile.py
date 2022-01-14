import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, MOTHERBOARD, \
    PROCESSOR, RAM, STORAGE_DRIVE, SOLID_STATE_DRIVE, EXTERNAL_STORAGE_DRIVE, \
    MEMORY_CARD, HEADPHONES, MOUSE, MONITOR, KEYBOARD, CPU_COOLER, \
    VIDEO_CARD, GAMING_CHAIR, NOTEBOOK, USB_FLASH_DRIVE, POWER_SUPPLY
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class ETChile(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOTHERBOARD,
            PROCESSOR,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MEMORY_CARD,
            HEADPHONES,
            MOUSE,
            MONITOR,
            KEYBOARD,
            CPU_COOLER,
            VIDEO_CARD,
            GAMING_CHAIR,
            NOTEBOOK,
            USB_FLASH_DRIVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['partes-y-piezas/psu-fuentes-de-poder', POWER_SUPPLY],
            ['partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/placas-madres', MOTHERBOARD],
            ['partes-y-piezas/procesadores', PROCESSOR],
            ['partes-y-piezas/memorias', RAM],
            ['partes-y-piezas/almacenamiento/discos-duros', STORAGE_DRIVE],
            ['almacenamiento-y-drives/hdd-interno', STORAGE_DRIVE],
            ['partes-y-piezas/almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['almacenamiento-y-drives/discos-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento-y-drives/ssd-externo',
             EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento-y-drives/ssd-interno-almacenamiento-y-drives',
             SOLID_STATE_DRIVE],
            ['partes-y-piezas/almacenamiento/ssd/ssd-interno/',
             SOLID_STATE_DRIVE],
            ['partes-y-piezas/almacenamiento/ssd/ssd-servers/',
             SOLID_STATE_DRIVE],
            ['accesorios-smartphones', MEMORY_CARD],
            ['almacenamiento-y-drives/memorias-flash', MEMORY_CARD],
            ['audio-y-streaming/audifonos', HEADPHONES],
            ['mouse-accesorios/mouse', MOUSE],
            ['monitores', MONITOR],
            ['teclados', KEYBOARD],
            ['partes-y-piezas/refrigeracion/ventiladores', CPU_COOLER],
            ['partes-y-piezas/refrigeracion/water-cooling', CPU_COOLER],
            ['partes-y-piezas/tarjetas-de-video', VIDEO_CARD],
            ['sillas', GAMING_CHAIR],
            ['notebooks/notebooks-gamers', NOTEBOOK],
            ['accesorios-usb', USB_FLASH_DRIVE],
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
                url_webpage = 'https://etchile.net/categorias/productos/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-small')

                if not product_containers:
                    if page == 1:
                        logging.warning('Emtpy category: ' + url_extension)
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
                    'attribute_color']
                sku = variation['sku']
                key = str(variation['variation_id'])
                stock = variation['max_qty']
                price = Decimal(variation['display_price'])
                picture_urls = [variation['image']['url']]

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
                    part_number=sku,
                    picture_urls=picture_urls,
                )
                products.append(p)
            return products

        else:
            sku = None
            if soup.find('span', 'sku'):
                sku = soup.find('span', 'sku').text
            key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                -1]

            stock_tag = soup.find('input', {'name': 'quantity'})
            if stock_tag:
                if 'max' in stock_tag.attrs:
                    stock = int(stock_tag['max'])
                else:
                    stock = 1
            else:
                stock = 0

            if soup.find('p', 'price').find('ins'):
                price = Decimal(
                    remove_words(
                        soup.find('p', 'price').find('ins').text.strip()))
            else:
                price = Decimal(
                    remove_words(soup.find('p', 'price').text.strip()))

            picture_urls = [tag.find('img')['data-src'].split('?')[0] for tag
                            in
                            soup.findAll('li', 'product_thumbnail_item')]
            description = html_to_markdown(
                str(soup.find('div', 'woocommerce-Tabs-panel--description')))
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
                description=description
            )
            return [p]
