import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, COMPUTER_CASE, \
    SOLID_STATE_DRIVE, RAM, MONITOR, MOUSE, GAMING_CHAIR, KEYBOARD, \
    POWER_SUPPLY, MOTHERBOARD, PROCESSOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['audifonos-ps4-xbox-one-y-switch', HEADPHONES],
            ['audifonos-home-oficce', HEADPHONES],
            # ['accesorios-para-pc-pc-gamer', HEADPHONES],
            ['gabinetes-gamer', COMPUTER_CASE],
            ['gabinetes-pc', COMPUTER_CASE],
            ['memorias-pendrives-disco-duro', SOLID_STATE_DRIVE],
            ['memorias-ram', RAM],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['mouse-ps4-xbox-one', MOUSE],
            ['sillas-gamer', GAMING_CHAIR],
            ['teclados', KEYBOARD],
            ['teclados-ps4-y-xbox-one', KEYBOARD],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['placas-madres', MOTHERBOARD],
            ['procesadores-de-pc', PROCESSOR]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            local_product_urls = []
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.crazygamesenchile.com/{}?page={}' \
                    .format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', {
                    'data-hook': 'product-list-grid-item'})
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                if len(product_containers) == len(local_product_urls):
                    break
                product_containers = product_containers[
                                     len(local_product_urls):
                                     len(product_containers) + 1]
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                    local_product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_container = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        name = json_container['name']
        sku_container = json.loads(
            soup.find('script', {'id': 'wix-warmup-data'}).text)
        sku_key_1 = list(sku_container['appsWarmupData'].keys())[0]
        sku_key_2 = list(sku_container['appsWarmupData'][sku_key_1].keys())[0]
        sku = sku_container['appsWarmupData'][sku_key_1][sku_key_2]['catalog'][
            'product']['id']
        if json_container['Offers'][
                'Availability'] == 'https://schema.org/OutOfStock':
            stock = 0
        else:
            stock = -1
        price = Decimal(json_container['Offers']['price'])
        picture_urls = [tag['src'] for tag in
                        soup.findAll('img', {'data-hook': 'thumbnail-image'})]
        if not picture_urls:
            picture_urls = [json_container['image']['contentUrl']]
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
