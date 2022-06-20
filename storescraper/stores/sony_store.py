import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import TELEVISION, CAMERA, STEREO_SYSTEM, \
    OPTICAL_DISK_PLAYER, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class SonyStore(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            CAMERA,
            STEREO_SYSTEM,
            OPTICAL_DISK_PLAYER,
            HEADPHONES,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['televisores-y-teatro-en-casa/televisores', TELEVISION],
            ['camaras/cyber-shot', CAMERA],
            ['audio/sistemas-de-audio', STEREO_SYSTEM],
            ['televisores-y-teatro-en-casa/reproductores-de-blu-ray-disc'
             '-y-dvd', OPTICAL_DISK_PLAYER],
            ['televisores-y-teatro-en-casa/teatro-en-casa', STEREO_SYSTEM],
            ['audio/audifonos', HEADPHONES],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://store.sony.cl/{}?PS=48'.format(
                url_extension)

            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            r = re.compile(r'Product:sp-(\d+$)')
            product_containers = json.loads(
                soup.find('template', {'data-varname': '__STATE__'}).find(
                    'script').text)
            product_container_keys = product_containers.keys()
            products_to_find = list(filter(r.match, product_container_keys))
            if not product_containers:
                logging.warning('Empty category: ' + url_extension)

            for product_key in products_to_find:
                product_url = product_containers[product_key]['link']
                product_urls.append('https://store.sony.cl' + product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_container = list(json.loads(
                soup.find('template', {'data-varname': '__STATE__'}).find(
                    'script').text).values())

        if len(json_container) == 0:
            return []

        json_container = json_container[0]
        api_url = 'https://store.sony.cl/api/catalog_system/pub/products' \
                  '/search?fq=productId:{}'.format(json_container['productId'])
        api_response = session.get(api_url)
        json_product = json.loads(api_response.text)[0]['items'][0]
        name = json_product['name']
        part_number = json_product['name'].replace('|', '').strip()
        sku = json_product['itemId']
        if json_product['sellers'][0]['commertialOffer']['AvailableQuantity'] \
                > 10:
            stock = 10
        else:
            stock = json_product['sellers'][0]['commertialOffer'][
                'AvailableQuantity']
        price = Decimal(
            json_product['sellers'][0]['commertialOffer']['Price'])
        picture_urls = [picture['imageUrl'].split('?v')[0] for picture
                        in json_product['images']]
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
            picture_urls=picture_urls
        )
        return [p]
