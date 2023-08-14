import html
import json
import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import STEREO_SYSTEM, MEMORY_CARD, \
    USB_FLASH_DRIVE, EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, RAM, HEADPHONES, \
    KEYBOARD, MOUSE, KEYBOARD_MOUSE_COMBO, COMPUTER_CASE, MONITOR, WEARABLE, \
    GAMING_CHAIR, CPU_COOLER, MOTHERBOARD, VIDEO_CARD, PROCESSOR, \
    POWER_SUPPLY, NOTEBOOK, TABLET, GAMING_DESK, MICROPHONE, \
    VIDEO_GAME_CONSOLE, SOLID_STATE_DRIVE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class SipoOnline(StoreWithUrlExtensions):
    url_extensions = [
        ['disipadores-cooler', CPU_COOLER],
        ['placa_madres', MOTHERBOARD],
        ['tarjeta_de_video', VIDEO_CARD],
        ['procesadores', PROCESSOR],
        ['fuente_poder', POWER_SUPPLY],
        ['monitor-gamer', MONITOR],
        ['gabinetes', COMPUTER_CASE],
        ['memoria-ram', RAM],
        ['parlante-musica', STEREO_SYSTEM],
        ['memorias', MEMORY_CARD],
        ['pendrives', USB_FLASH_DRIVE],
        ['disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
        ['hdd-disco-duro', STORAGE_DRIVE],
        ['ssd-unidad-estado-solido',
         SOLID_STATE_DRIVE],
        ['audifonos', HEADPHONES],
        ['parlantes-pc', STEREO_SYSTEM],
        ['audifono-pc', HEADPHONES],
        ['teclado', KEYBOARD],
        ['mouse', MOUSE],
        ['combo-computacion', KEYBOARD_MOUSE_COMBO],
        ['consolas', VIDEO_GAME_CONSOLE],
        ['silla-gamer', GAMING_CHAIR],
        ['audifono-gamer', HEADPHONES],
        ['teclado-gamer', KEYBOARD],
        ['mouse-gamer', MOUSE],
        ['kit-gamer', KEYBOARD_MOUSE_COMBO],
        ['smartwatch', WEARABLE],
        ['notebooks', NOTEBOOK],
        ['tablets', TABLET],
        ['microfono', MICROPHONE],
        ['escritorio-gamer', GAMING_DESK]
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://sipoonline.cl/product-category/' \
                          '{}/page/{}/'.format(url_extension, page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            main = soup.find('main', 'site-main')
            if not main:
                if page == 1:
                    print(url_webpage)
                    import ipdb
                    ipdb.set_trace()
                    logging.warning('Empty category: ' + url_extension)
                break
            product_containers = soup.findAll('li', 'product')
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

        product_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'})
                .text)
        if '@graph' not in product_data:
            return []

        product_data = product_data['@graph'][1]

        name = product_data['name']
        description = product_data['description']
        is_reserva = 'VENTA' in description.upper()
        variants = soup.find('form', 'variations_form')
        if not variants:
            variants = soup.find('div', 'variations_form')

        if variants:
            products = []
            container_products = json.loads(
                html.unescape(variants['data-product_variations']))
            for product in container_products:
                if len(product['attributes']) > 0:
                    variant_name = name + " - " + next(
                        iter(product['attributes'].values()))
                else:
                    variant_name = name
                sku = str(product['variation_id'])

                if is_reserva:
                    stock = 0
                elif product['availability_html'] != '':
                    stock = int(
                        BeautifulSoup(product['availability_html'],
                                      'html.parser').text.split()[0])
                else:
                    stock = -1
                normal_price = Decimal(product['display_price'])
                if soup.find('p', 'price').text == '':
                    offer_price = (
                        normal_price * Decimal('0.98004')).quantize(0)
                else:
                    offer_price = normal_price
                picture_urls = [product['image']['src']]
                p = Product(
                    variant_name,
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
                    picture_urls=picture_urls,
                    description=description
                )
                products.append(p)
            return products
        else:
            stock_container = soup.find('p', 'stock in-stock')
            if is_reserva:
                stock = 0
            elif stock_container:
                stock = int(stock_container.text.split()[0])
            elif soup.find('p', 'stock out-of-stock'):
                stock = 0
            else:
                stock = -1
            sku = soup.find(
                'link', {'rel': 'shortlink'})['href'].split('p=')[1]
            normal_price = Decimal(product_data['offers'][0]['price'])
            if soup.find('p', 'price').text == '':
                offer_price = (normal_price * Decimal('0.98004')).quantize(0)
            else:
                offer_price = normal_price
            picture_containers = soup.find('ul',
                                           'swiper-wrapper') \
                .findAll('img')
            picture_urls = [tag['src'] for tag in picture_containers
                            if validators.url(tag['src'])]
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
                picture_urls=picture_urls,
                description=description
            )
            return [p]
