import html
import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import WEARABLE, HEADPHONES, STEREO_SYSTEM, \
    USB_FLASH_DRIVE, KEYBOARD, MONITOR, POWER_SUPPLY, COMPUTER_CASE, MOUSE, \
    GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class VGamers(Store):
    @classmethod
    def categories(cls):
        return [
            WEARABLE,
            HEADPHONES,
            STEREO_SYSTEM,
            USB_FLASH_DRIVE,
            KEYBOARD,
            MONITOR,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOUSE,
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['smartwatch', WEARABLE],
            ['audifonos', HEADPHONES],
            ['parlantes', STEREO_SYSTEM],
            ['almacenamiento', USB_FLASH_DRIVE],
            ['teclados-y-mouse', KEYBOARD],
            ['monitores-gamer', MONITOR],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinete-gamer', COMPUTER_CASE],
            ['mouse-gamer', MOUSE],
            # GAMER KEYBOARD
            ['teclados-gamer', KEYBOARD],
            # GAMER HEADPHONES
            ['audifonos-gamer', HEADPHONES],
            ['sillas-gamer', GAMING_CHAIR]
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
                url_webpage = 'https://vgamers.cl/collections/' \
                              '{}?page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('a', 'product-card__link '
                                                       'product'
                                                       '-card__switchImage')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
                    product_urls.append('https://vgamers.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_info = json.loads(html.unescape(soup.find('script', {
            'id': 'ProductJson-product-template-2'}).text))
        picture_containers = product_info['images']
        picture_urls = ['https:' + url.split('?')[0] for url in
                        picture_containers]
        if len(product_info['variants']) > 1:
            products = []
            for variant in product_info['variants']:
                name = variant['name']
                sku = str(variant['id'])
                stock = -1 if variant['available'] else 0
                price = Decimal(variant['price'] / 100)
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
                    picture_urls=picture_urls

                )
                products.append(p)
            return products
        else:
            name = product_info['title']
            sku = str(product_info['id'])
            stock = -1 if product_info['available'] else 0
            price = Decimal(product_info['price'] / 100)

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
                picture_urls=picture_urls

            )
            return [p]
