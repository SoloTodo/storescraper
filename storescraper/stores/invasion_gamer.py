import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, PROCESSOR, RAM, \
    MOTHERBOARD, VIDEO_CARD, SOLID_STATE_DRIVE, CPU_COOLER, POWER_SUPPLY, \
    KEYBOARD, MOUSE, HEADPHONES, GAMING_CHAIR, NOTEBOOK, MONITOR, \
    KEYBOARD_MOUSE_COMBO, STEREO_SYSTEM, VIDEO_GAME_CONSOLE, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class InvasionGamer(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            PROCESSOR,
            RAM,
            MOTHERBOARD,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            CPU_COOLER,
            POWER_SUPPLY,
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            GAMING_CHAIR,
            NOTEBOOK,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            STEREO_SYSTEM,
            VIDEO_GAME_CONSOLE,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gabinetes', COMPUTER_CASE],
            ['procesadores', PROCESSOR],
            ['procesador-intel', PROCESSOR],
            ['procesador-amd', PROCESSOR],
            ['memoria-ram', RAM],
            ['placas-madre', MOTHERBOARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['refrigeracion', CPU_COOLER],
            ['fuente-de-poder', POWER_SUPPLY],
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['audifonos', HEADPHONES],
            ['sillas', GAMING_CHAIR],
            ['set', KEYBOARD_MOUSE_COMBO],
            ['sonido', STEREO_SYSTEM],
            ['portatiles', NOTEBOOK],
            ['monitores', MONITOR],
            ['joysticks-pc', VIDEO_GAME_CONSOLE],
            ['microfono', MICROPHONE]
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
                url_webpage = 'https://invasiongamer.com/collections/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://invasiongamer.com' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        picture_urls = ['https:' + tag['data-src'].replace('_130x', '')
                        .split('?')[0] for tag in soup
                        .find('div', 'product-gallery__thumbnail-list')
                        .findAll('img')]

        product_data_tag = soup.find('script', {'type': 'application/ld+json'})
        product_data = json.loads(product_data_tag.text)
        base_name = product_data['name']

        if 'PREVENTA' in base_name.upper():
            force_unavailable = True
        else:
            force_unavailable = False

        products = []

        for variant in product_data['offers']:
            variant_name = '{} ({})'.format(base_name, variant['name'])
            variant_price = Decimal(variant['price'])
            variant_url = 'https://invasiongamer.com' + variant['url']
            variant_sku = variant['url'].split('?variant=')[1]

            if force_unavailable:
                variant_stock = 0
            elif variant['availability'] == 'https://schema.org/InStock':
                variant_stock = -1
            else:
                variant_stock = 0

            p = Product(
                variant_name,
                cls.__name__,
                category,
                variant_url,
                url,
                variant_sku,
                variant_stock,
                variant_price,
                variant_price,
                'CLP',
                sku=variant_sku,
                picture_urls=picture_urls,
            )
            products.append(p)
        return products
