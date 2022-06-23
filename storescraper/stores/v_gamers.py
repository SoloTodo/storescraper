import html
import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, KEYBOARD_MOUSE_COMBO, \
    STEREO_SYSTEM, KEYBOARD, MONITOR, POWER_SUPPLY, COMPUTER_CASE, MOUSE, \
    GAMING_CHAIR, CPU_COOLER, VIDEO_CARD, STORAGE_DRIVE, MOTHERBOARD, \
    PROCESSOR, RAM, GAMING_DESK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class VGamers(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            STEREO_SYSTEM,
            KEYBOARD,
            MONITOR,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOUSE,
            GAMING_CHAIR,
            CPU_COOLER,
            VIDEO_CARD,
            STORAGE_DRIVE,
            MOTHERBOARD,
            RAM,
            GAMING_DESK,
            KEYBOARD_MOUSE_COMBO,
            PROCESSOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['teclados', KEYBOARD],
            ['zona-gamer/mouse', MOUSE],
            ['escritorio', GAMING_DESK],
            ['sillas', GAMING_CHAIR],
            ['sillones', GAMING_CHAIR],
            ['zona-gamer/kit-gamer', KEYBOARD_MOUSE_COMBO],
            ['hardware/almacenamiento', STORAGE_DRIVE],
            ['hardware/fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['hardware/memorias-ram', RAM],
            ['hardware/placas-madres', MOTHERBOARD],
            ['hardware/procesadores', PROCESSOR],
            ['hardware/refrigeracion', CPU_COOLER],
            ['hardware/tarjetas-graficas', VIDEO_CARD],
            ['monitores', MONITOR],
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
                url_webpage = 'https://vgamers.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'wf-cell')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('button', {'name': 'add-to-cart'})['value']

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        name = json_data['name']
        sku = json_data['sku']
        description = json_data['description']
        offer_price = Decimal(json_data['offers'][0]['price'])
        normal_price = (offer_price * Decimal(1.05)).quantize(Decimal("0.0"))

        if not soup.find('button', 'single_add_to_cart_button'):
            stock = 0
        else:
            qty_input = soup.find('input', 'qty')
            if qty_input['type'] == 'hidden':
                stock = 1
            elif 'max' in qty_input.attrs and qty_input['max'] != '':
                stock = int(qty_input['max'])
            else:
                stock = -1

        picture_urls = []
        picture_container = soup.find('div', 'woocommerce-product-gallery')
        for p in picture_container.findAll('a', 'wcgs-slider-image'):
            if p['href'] not in picture_urls:
                picture_urls.append(p['href'])

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
            description=description

        )
        return [p]
