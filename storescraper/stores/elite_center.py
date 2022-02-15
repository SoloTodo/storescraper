import json
import re
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import HEADPHONES, SOLID_STATE_DRIVE, \
    MOUSE, KEYBOARD, CPU_COOLER, COMPUTER_CASE, \
    POWER_SUPPLY, RAM, MONITOR, MOTHERBOARD, \
    PROCESSOR, VIDEO_CARD, STEREO_SYSTEM, STORAGE_DRIVE, VIDEO_GAME_CONSOLE, \
    GAMING_CHAIR, NOTEBOOK, EXTERNAL_STORAGE_DRIVE, GAMING_DESK, MICROPHONE
from storescraper.utils import session_with_proxy, remove_words


class EliteCenter(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            STEREO_SYSTEM,
            STORAGE_DRIVE,
            MOUSE,
            KEYBOARD,
            SOLID_STATE_DRIVE,
            CPU_COOLER,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            VIDEO_GAME_CONSOLE,
            GAMING_CHAIR,
            NOTEBOOK,
            EXTERNAL_STORAGE_DRIVE,
            GAMING_DESK,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['escritorios', GAMING_DESK],
            ['microfonos', MICROPHONE],
            ['parlantes', STEREO_SYSTEM],
            ['disco-externo', EXTERNAL_STORAGE_DRIVE],
            ['procesadores', PROCESSOR],
            ['placas-madres', MOTHERBOARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['memorias-ram', RAM],
            ['fuente-de-poder', POWER_SUPPLY],
            ['refrigeracion', CPU_COOLER],
            ['gabinetes', COMPUTER_CASE],
            ['disco-duro-pc-hdd', STORAGE_DRIVE],
            ['disco-estado-solido-ssd', SOLID_STATE_DRIVE],
            ['monitores', MONITOR],
            ['sillas-gamer', GAMING_CHAIR],
            ['notebooks', NOTEBOOK],
            ['consolas', VIDEO_GAME_CONSOLE],
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

                url_webpage = 'https://elitecenter.cl/product-category/a/' \
                              '?paged={}&yith_wcan=1&product_cat={}' \
                              '&instock_filter=1'.format(
                                page, url_extension)
                print(url_webpage)
                response = session.get(url_webpage)

                if response.status_code == 404:
                    # if page == 1:
                    #     raise Exception('Invalid category: ' + url_extension)
                    break

                data = response.text
                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.findAll('div', 'product-grid-item')

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

        json_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)

        for json_entry in json_data['@graph']:
            if json_entry['@type'] == 'Product':
                product_data = json_entry
                break
        else:
            raise Exception('No product data found')

        name = product_data['name']
        sku = product_data['sku']
        offer_price = Decimal(product_data['offers']['price'])
        normal_price = (offer_price * Decimal('1.05')).quantize(0)

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]

        if soup.find('button', 'stock_alert_button'):
            stock = 0
        else:
            stock_tag = soup.find('p', 'stock')
            if stock_tag:
                stock = int(re.search(r'(\d+)', stock_tag.text).groups()[0])
            else:
                stock = -1

        picture_urls = [tag['href'].split('?')[0] for tag in
                        soup.find(
                            'figure', 'woocommerce-product-gallery__wrapper')
                        .findAll('a')
                        if validators.url(tag['href'])
                        ]

        description = product_data['description']
        part_number = soup.find(
            'div', {'data-id': '1072e30'}).text.split(': ')[1].strip()

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
            part_number=part_number,
            picture_urls=picture_urls,
            description=description

        )
        return [p]
