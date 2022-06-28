from decimal import Decimal
import json
import logging
import validators

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, \
    KEYBOARD_MOUSE_COMBO, MICROPHONE, MONITOR, MOTHERBOARD, MOUSE, KEYBOARD, \
    HEADPHONES, COMPUTER_CASE, PROCESSOR, RAM, SOLID_STATE_DRIVE, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PlayFactory(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            RAM,
            COMPUTER_CASE,
            MONITOR,
            GAMING_CHAIR,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            MOUSE,
            MICROPHONE,
            KEYBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes/placa-madre', MOTHERBOARD],
            ['componentes/procesadores-componentes', PROCESSOR],
            ['componentes/tarjeta-de-video', VIDEO_CARD],
            ['componentes/almacenamiento', SOLID_STATE_DRIVE],
            ['componentes/memoria-ram', RAM],
            ['computacion/gabinetes-pc', COMPUTER_CASE],
            ['computacion/monitores-computacion', MONITOR],
            ['mobiliario/sillas-gamer-mobiliario', GAMING_CHAIR],
            ['zona-gamer/audifonos-zona-gamer', HEADPHONES],
            ['zona-gamer/kit-teclado-mouse', KEYBOARD_MOUSE_COMBO],
            ['zona-gamer/mouse', MOUSE],
            ['zona-gamer/streaming/microfonos-streaming', MICROPHONE],
            ['zona-gamer/teclados-zona-gamer', KEYBOARD],
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
                url_webpage = 'https://www.playfactory.cl/categoria-producto' \
                              '/{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                if '404!' in soup.text:
                    break
                product_containers = soup.findAll(
                    'li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find(
                        'a',
                        'woocommerce-LoopProduct-link ' +
                        'woocommerce-loop-product__link'
                    )['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        soup_jsons = soup.findAll(
            'script', {'type': 'application/ld+json'})

        if len(soup_jsons) <= 1:
            return []

        json_data = json.loads(soup_jsons[1].text)['@graph'][0]
        base_name = json_data['name']

        picture_urls = []
        figures = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        for a in figures.findAll('img'):
            if validators.url(a['src']):
                picture_urls.append(a['src'])

        products = []
        variants_form = soup.find('form', 'variations_form cart')
        if variants_form:
            varaints_json = json.loads(
                variants_form['data-product_variations'])
            for variant in varaints_json:
                var_name = ""
                for key in variant['attributes']:
                    var_name += ' - ' + variant['attributes'][key]
                name = base_name + var_name
                price = Decimal(variant['display_price'])

                sku = variant['sku']
                stock = variant['max_qty']

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
                    picture_urls=picture_urls,
                )
                products.append(p)

            return products
        else:
            sku = soup.find('link', {'rel': 'shortlink'})[
                'href'].split('?p=')[-1]
            price = Decimal(json_data['offers'][0]['price'])
            stock = 0
            qty_input = soup.find('input', 'qty')
            if qty_input:
                if 'type' in qty_input.attrs and qty_input['type'] == "hidden":
                    stock = 1
                elif 'max' in qty_input.attrs and qty_input['max'] != "":
                    stock = int(qty_input['max'])
                else:
                    stock = 1

            p = Product(
                base_name,
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
                picture_urls=picture_urls,
            )
            return [p]
