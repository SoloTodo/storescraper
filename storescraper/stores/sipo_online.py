import html
import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STEREO_SYSTEM, MEMORY_CARD, \
    USB_FLASH_DRIVE, EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, RAM, HEADPHONES, \
    KEYBOARD, MOUSE, KEYBOARD_MOUSE_COMBO, COMPUTER_CASE, MONITOR, WEARABLE, \
    GAMING_CHAIR, CPU_COOLER, MOTHERBOARD, VIDEO_CARD, PROCESSOR, \
    POWER_SUPPLY, NOTEBOOK, TABLET, GAMING_DESK, MICROPHONE, \
    VIDEO_GAME_CONSOLE, SOLID_STATE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class SipoOnline(Store):
    @classmethod
    def categories(cls):
        return [
            STEREO_SYSTEM,
            MEMORY_CARD,
            PROCESSOR,
            USB_FLASH_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            RAM,
            HEADPHONES,
            KEYBOARD,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            COMPUTER_CASE,
            MONITOR,
            WEARABLE,
            GAMING_CHAIR,
            CPU_COOLER,
            MOTHERBOARD,
            VIDEO_CARD,
            POWER_SUPPLY,
            NOTEBOOK,
            TABLET,
            GAMING_DESK,
            MICROPHONE,
            VIDEO_GAME_CONSOLE,
            SOLID_STATE_DRIVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-pc/disipadores-cooler', CPU_COOLER],
            ['componentes-pc/placa_madres', MOTHERBOARD],
            ['componentes-pc/tarjeta_de_video', VIDEO_CARD],
            ['componentes-pc/procesadores', PROCESSOR],
            ['componentes-pc/fuente_poder', POWER_SUPPLY],
            ['gamers-y-streaming/monitor-gamer', MONITOR],
            ['componentes-pc/gabinetes', COMPUTER_CASE],
            ['componentes-pc/memoria-ram', RAM],
            ['parlante-musica', STEREO_SYSTEM],
            ['almacenamiento/memorias', MEMORY_CARD],
            ['almacenamiento/pendrives', USB_FLASH_DRIVE],
            ['almacenamiento/disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
            ['componentes-pc/disco-interno/hdd-disco-duro', STORAGE_DRIVE],
            ['componentes-pc/disco-interno/ssd-unidad-estado-solido',
             SOLID_STATE_DRIVE],
            ['audifonos', HEADPHONES],
            ['computacion/parlantes-pc', STEREO_SYSTEM],
            ['computacion/audifono-pc', HEADPHONES],
            ['computacion/teclado', KEYBOARD],
            ['computacion/mouse', MOUSE],
            ['computacion/combo-computacion', KEYBOARD_MOUSE_COMBO],
            ['zona-gamer/consolas', VIDEO_GAME_CONSOLE],
            ['zona-gamer/silla-gamer', GAMING_CHAIR],
            ['zona-gamer/audifono-gamer', HEADPHONES],
            ['zona-gamer/teclado-gamer', KEYBOARD],
            ['zona-gamer/mouse-gamer', MOUSE],
            ['zona-gamer/kit-gamer', KEYBOARD_MOUSE_COMBO],
            ['smartwatch', WEARABLE],
            ['computadores/notebooks', NOTEBOOK],
            ['tablets', TABLET],
            ['parlante-musica/microfono', MICROPHONE],
            ['zona-gamer/escritorio-gamer', GAMING_DESK]
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

                if product['availability_html'] != '':
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
            if stock_container:
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
            picture_urls = [tag['src'] for tag in picture_containers]
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
