from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, GAMING_CHAIR, HEADPHONES, \
    KEYBOARD, MONITOR, NOTEBOOK, PRINTER, STEREO_SYSTEM, TABLET, TELEVISION, \
    VIDEO_GAME_CONSOLE, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Dreamtec(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            NOTEBOOK,
            VIDEO_GAME_CONSOLE,
            HEADPHONES,
            GAMING_CHAIR,
            KEYBOARD,
            ALL_IN_ONE,
            PRINTER,
            TELEVISION,
            STEREO_SYSTEM,
            TABLET,
            WEARABLE,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gamer-zone/monitores-gamer-zone', MONITOR],
            ['gamer-zone/notebook-gamers', NOTEBOOK],
            ['gamer-zone/consola-gamer-zone', VIDEO_GAME_CONSOLE],
            ['gamer-zone/audifonos-gamer-gamer-zone', HEADPHONES],
            ['gamer-zone/silla-gamer-gamer-zone', GAMING_CHAIR],
            ['gamer-zone/accesorios-gamer-gamer-zone', KEYBOARD],
            ['home-office/monitores-home-office', MONITOR],
            ['ome-office/notebooks-home-office', NOTEBOOK],
            ['home-office/macbook', NOTEBOOK],
            ['home-office/all-in-one-home-office', ALL_IN_ONE],
            ['home-office/impresoras', PRINTER],
            ['home-office/escaner', PRINTER],
            ['home-office/accesorios-home-officie', KEYBOARD],
            ['smart-home/smart-tv-smart-home', TELEVISION],
            ['smart-home/soundbar-smat-home', STEREO_SYSTEM],
            ['smart-home/tablets-smart-home', TABLET],
            ['smart-home/ipad-smart-home', TABLET],
            ['smart-home/smartwatch-smart-home', WEARABLE],
            ['smart-home/audifonos', HEADPHONES],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.dreamtec.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('section', 'product')
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
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        if '@graph' not in json_data:
            return []

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        description = product_data['description']
        sku = str(product_data['sku'])
        price = Decimal(product_data['offers'][0]['price'])

        qty_input = soup.find('input', 'input-text qty text')
        if qty_input:
            if qty_input['max']:
                stock = int(qty_input['max'])
            else:
                stock = -1
        else:
            if soup.find('button', 'single_add_to_cart_button'):
                stock = 1
            else:
                stock = 0

        picture_urls = []
        picture_container = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        for a in picture_container.findAll('a'):
            picture_urls.append(a['href'])

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
            picture_urls=picture_urls,
            description=description
        )
        return [p]
