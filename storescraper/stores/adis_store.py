from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, CELL, HEADPHONES, KEYBOARD, \
    KEYBOARD_MOUSE_COMBO, MOUSE, NOTEBOOK, TABLET
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class AdisStore(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            MOUSE,
            KEYBOARD,
            NOTEBOOK,
            ALL_IN_ONE,
            TABLET,
            CELL
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios-y-perifericos/auriculares-y-manos-libres',
                HEADPHONES],
            ['accesorios-y-perifericos/combos-de-teclado-y-mouses',
                KEYBOARD_MOUSE_COMBO],
            ['accesorios-y-perifericos/mouses', MOUSE],
            ['accesorios-y-perifericos/teclados-y-teclados-de-numeros',
                KEYBOARD],
            ['computadores-y-notebooks/notebooks', NOTEBOOK],
            ['computadores-y-notebooks/all-in-one', ALL_IN_ONE],
            ['computadores-y-notebooks/pc-de-escritorio', ALL_IN_ONE],
            ['computadores-y-notebooks/tablets', TABLET],
            ['audio-video-tecnologia/celulares', CELL],
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
                url_webpage = 'https://adis-store.cl/categoria/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if 'shop' in product_url:
                        product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        shortlink = soup.find('link', {'rel': 'shortlink'})

        if not shortlink:
            return []

        key = shortlink['href'].split('p=')[1]

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)['@graph'][-1]
        name = json_data['name'][:256]
        sku = json_data['sku']

        if 'description' in json_data:
            description = json_data['description']
        else:
            description = None

        price = Decimal(str(soup.find(
            'span', 'woocommerce-Price-amount')
            .find('bdi').text.replace('$', '').replace('.', '')))
        part_number = soup.find('span', 'stl_codenum').text.strip()

        quantity_tag = soup.find('div', 'qty-box')

        if quantity_tag:
            input_stock = quantity_tag.find('input')
            if input_stock['max']:
                stock = int(input_stock['max'])
            else:
                stock = -1
        else:
            stock = -1

        picture_urls = []
        picture_container = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        for i in picture_container.findAll('img'):
            picture_urls.append(i['src'])

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
            description=description,
            part_number=part_number
        )
        return [p]
