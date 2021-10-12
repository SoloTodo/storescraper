import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import UPS, COMPUTER_CASE, MOTHERBOARD, PROCESSOR, \
    RAM, STORAGE_DRIVE, SOLID_STATE_DRIVE, EXTERNAL_STORAGE_DRIVE, MEMORY_CARD, \
    HEADPHONES, MOUSE, MONITOR, KEYBOARD, CPU_COOLER, VIDEO_CARD, GAMING_CHAIR, \
    NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class ETChile(Store):
    @classmethod
    def categories(cls):
        return [
            UPS,
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
            NOTEBOOK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['partes-y-piezas/psu-fuentes-de-poder', UPS],
            ['partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/placas-madres', MOTHERBOARD],
            ['partes-y-piezas/procesadores', PROCESSOR],
            ['partes-y-piezas/memorias', RAM],
            ['partes-y-piezas/almacenamiento/discos-duros', STORAGE_DRIVE],
            ['partes-y-piezas/almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['almacenamiento-y-drives/discos-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento-y-drives/ssd-interno-almacenamiento-y-drives',
             SOLID_STATE_DRIVE],
            ['almacenamiento-y-drives/memorias-flash', MEMORY_CARD],
            ['audio-y-streaming/audifonos', HEADPHONES],
            ['mouse-accesorios/mouse', MOUSE],
            ['monitores', MONITOR],
            ['teclados', KEYBOARD],
            ['partes-y-piezas/refrigeracion', CPU_COOLER],
            ['partes-y-piezas/tarjetas-de-video', VIDEO_CARD],
            ['sillas', GAMING_CHAIR],
            ['notebooks', NOTEBOOK],
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
                part_number = variation['sku']
                sku = str(variation['variation_id'])
                if variation['is_in_stock']:
                    stock = -1
                else:
                    stock = 0
                price = Decimal(variation['display_price'])
                picture_urls = [variation['image']['url']]
                p = Product(
                    variation_name,
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
                )
                products.append(p)
            return products

        else:
            part_number = None
            if soup.find('span', 'sku'):
                part_number = soup.find('span', 'sku').text
            sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                -1]
            if soup.find('p', 'stock in-stock'):
                stock = -1
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
            )
            return [p]
