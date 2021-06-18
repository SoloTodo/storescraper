import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, KEYBOARD, MONITOR, HEADPHONES, \
    KEYBOARD_MOUSE_COMBO, COMPUTER_CASE, RAM, GAMING_CHAIR, STEREO_SYSTEM, \
    TABLET, EXTERNAL_STORAGE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class GGames(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            MONITOR,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            RAM,
            COMPUTER_CASE,
            GAMING_CHAIR,
            STEREO_SYSTEM,
            TABLET,
            EXTERNAL_STORAGE_DRIVE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['mouse/gamer', MOUSE],
            ['mouse/homeoffice', MOUSE],
            ['teclado/gamer', KEYBOARD],
            ['teclado/homeoffice', KEYBOARD],
            ['monitores', MONITOR],
            ['headsets/gamer', HEADPHONES],
            ['lifestyle/audífonos', HEADPHONES],
            ['headsets/homeoffice', HEADPHONES],
            ['combos/gamer', KEYBOARD_MOUSE_COMBO],
            ['combos/homeoffice', KEYBOARD_MOUSE_COMBO],
            ['componentes-pc', RAM],
            ['gabinete', COMPUTER_CASE],
            ['sillas-gamers', GAMING_CHAIR],
            ['parlantes-1', STEREO_SYSTEM],
            ['lifestyle/parlante+bluetooth', STEREO_SYSTEM],
            ['tablet', TABLET],
            ['hd-portatil', EXTERNAL_STORAGE_DRIVE]
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

                url_webpage = 'https://ggames.cl/collections/{}?page={}' \
                    .format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)

                data = response.text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'grid__item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://ggames.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        picture_urls = ['http:' + tag['src'].split('?v')[0] for tag in
                        soup.find('div', 'product-single').
                        find('div', 'grid__item').findAll('img')
                        if tag.has_attr('src')]
        if 'AGOTADO' in soup.find('dl', 'price').text.strip():
            stock = 0
        else:
            stock = -1
        json_container = json.loads(soup.find('script', {
            'id': 'ProductJson-product-template'}).text.strip())
        products = []
        name = json_container['title']

        for variant in json_container['variants']:
            variant_name = '{} {}'.format(name, variant['title']).strip()
            part_number = variant['sku']
            sku = str(variant['id'])
            price = Decimal(variant['price'] / 100)
            p = Product(
                variant_name,
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
                picture_urls=picture_urls,
            )
            products.append(p)
        return products
