import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_DESK, HEADPHONES, COMPUTER_CASE, \
    MICROPHONE, SOLID_STATE_DRIVE, RAM, MONITOR, MOUSE, GAMING_CHAIR, \
    KEYBOARD, POWER_SUPPLY, MOTHERBOARD, PROCESSOR, STEREO_SYSTEM, \
    USB_FLASH_DRIVE, VIDEO_CARD, CPU_COOLER, EXTERNAL_STORAGE_DRIVE, \
    VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class CrazyGamesenChile(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            COMPUTER_CASE,
            SOLID_STATE_DRIVE,
            RAM,
            MONITOR,
            MOUSE,
            GAMING_CHAIR,
            KEYBOARD,
            POWER_SUPPLY,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            CPU_COOLER,
            EXTERNAL_STORAGE_DRIVE,
            VIDEO_GAME_CONSOLE,
            MICROPHONE,
            STEREO_SYSTEM,
            GAMING_DESK,
            USB_FLASH_DRIVE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos-gamers', HEADPHONES],
            ['audifonos', HEADPHONES],
            ['audifonos-home-office', HEADPHONES],
            ['microfonos', MICROPHONE],
            ['parlantes', STEREO_SYSTEM],
            ['teclados-ps4-y-xbox-one', KEYBOARD],
            ['teclados', KEYBOARD],
            ['mouse-gamer', MOUSE],
            ['mouse', MOUSE],
            ['monitores', MONITOR],
            ['escritorios-gamer', GAMING_DESK],
            ['sillas-gamer', GAMING_CHAIR],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes-pc', COMPUTER_CASE],
            ['gabinetes-gamer', COMPUTER_CASE],
            ['memorias-ram', RAM],
            ['placas-madres', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['fan-cooler-pc', CPU_COOLER],
            ['discos-duros-internos', SOLID_STATE_DRIVE],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['memorias-pendrives', USB_FLASH_DRIVE],
            ['consolas', VIDEO_GAME_CONSOLE],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.crazygamesenchile.com/{}?page=20' \
                .format(url_extension)
            print(url_webpage)
            res = session.get(url_webpage)

            if res.status_code == 404:
                raise Exception('Invalid category: ' + url_extension)

            soup = BeautifulSoup(res.text, 'html.parser')
            product_containers = soup.findAll('li', {
                'data-hook': 'product-list-grid-item'})
            if not product_containers:
                logging.warning('Empty category: ' + url_extension)
                continue
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        sku_container = json.loads(
            soup.find('script', {'id': 'wix-warmup-data'}).text)
        sku_key_1 = list(sku_container['appsWarmupData'].keys())[0]
        sku_key_2 = list(sku_container['appsWarmupData'][sku_key_1].keys())[0]
        product_data = sku_container['appsWarmupData'][sku_key_1][
            sku_key_2]['catalog']['product']
        base_name = product_data['name']
        description = html_to_markdown(product_data['description'])
        base_picture_urls = [x['fullUrl'] for x in product_data['media']]
        if len(product_data['productItems']) > 1:
            assert len(product_data['options']) == 1
            variation_options = {x['id']: x for x in product_data[
                'options'][0]['selections']}
            products = []

            for sku_data in product_data['productItems']:
                variation_key = sku_data['id']
                variation_sku = sku_data['sku'] or None
                variation_stock = sku_data['inventory']['quantity']
                variation_price = Decimal(sku_data['comparePrice']) or \
                    Decimal(sku_data['price'])
                assert variation_price or not variation_stock
                assert len(sku_data['optionsSelections']) == 1
                variation_option_key = sku_data['optionsSelections'][0]
                variation_option = variation_options[variation_option_key]
                variation_name = '{} - ({})'.format(
                    base_name, variation_option['key'])
                picture_urls = [x['fullUrl'] for x in
                                variation_option['linkedMediaItems'] or []]
                p = Product(
                    variation_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    variation_key,
                    variation_stock,
                    variation_price,
                    variation_price,
                    'CLP',
                    sku=variation_sku,
                    picture_urls=picture_urls or base_picture_urls,
                    description=description
                )
                products.append(p)
            return products

        else:
            assert len(product_data['productItems']) == 1
            price = Decimal(product_data['discountedPrice'])
            key = product_data['id']
            sku = product_data['sku']
            stock = product_data['inventory']['quantity']
            assert price or not stock
            p = Product(
                base_name,
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
                picture_urls=base_picture_urls,
                description=description
            )
            return [p]
