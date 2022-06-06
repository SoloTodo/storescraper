import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import WEARABLE, KEYBOARD, STEREO_SYSTEM, \
    MONITOR, MOUSE, USB_FLASH_DRIVE, GAMING_CHAIR, HEADPHONES, \
    KEYBOARD_MOUSE_COMBO
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class VStore(Store):
    @classmethod
    def categories(cls):
        return [
            WEARABLE,
            KEYBOARD,
            STEREO_SYSTEM,
            MONITOR,
            MOUSE,
            USB_FLASH_DRIVE,
            GAMING_CHAIR,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['smartwatch', WEARABLE],
            ['teclados', KEYBOARD],
            ['parlantes', STEREO_SYSTEM],
            ['conexion-y-video', MONITOR],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['almacenamiento', USB_FLASH_DRIVE],
            ['sillas-de-oficina', GAMING_CHAIR],
            ['audifonos', HEADPHONES],
            ['pack-de-productos/COMBO', KEYBOARD_MOUSE_COMBO],
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
                url_webpage = 'https://www.vstore.cl/collections/{}?page={}'. \
                    format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('h4', 'product-card__title')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://www.vstore.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_container = json.loads(soup.find('script', {
            'id': 'ProductJson-product-template-2'}).text.strip())
        name = json_container['title']
        key = str(json_container['id'])
        json_product = json_container['variants'][0]
        sku = json_product['sku']
        if json_product['available']:
            stock = -1
        else:
            stock = 0
        price = (Decimal(json_product['price']) / Decimal(100)).quantize(0)
        picture_urls = [m['src'] for m in json_container['media']]

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
            picture_urls=picture_urls
        )
        return [p]
