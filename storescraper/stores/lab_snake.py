from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import COMPUTER_CASE, CPU_COOLER, GAMING_CHAIR, \
    HEADPHONES, KEYBOARD, MICROPHONE, MOUSE, PROCESSOR, SOLID_STATE_DRIVE, \
    VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LabSnake(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            MOUSE,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            HEADPHONES,
            KEYBOARD,
            GAMING_CHAIR,
            CPU_COOLER,
            MICROPHONE,
            COMPUTER_CASE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['procesadores', PROCESSOR],
            ['mouse', MOUSE],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['audifonos', HEADPHONES],
            ['teclados', KEYBOARD],
            ['sillas', GAMING_CHAIR],
            ['refrigeracion', CPU_COOLER],
            ['microfonos', MICROPHONE],
            ['gabinetes', COMPUTER_CASE],
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
                url_webpage = 'https://labsnake.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_a = soup.findAll('a', 'product-image')
                if not product_a:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for a in product_a:
                    product_url = 'https://labsnake.cl' + a['href']
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
        base_name = json_data['name']
        description = json_data['description']
        price = Decimal(json_data['offers']['price'])

        picture_urls = []
        picture_div = soup.find('div', 'product-images')
        for picture in picture_div.findAll('img', 'img-fluid'):
            picture_urls.append(picture['src'])

        div_with_variations = soup.find('div', 'field-group')
        if div_with_variations:
            products = []
            variations = div_with_variations.findAll('option')
            for variation in variations:
                name = base_name + ' - ' + variation.text.strip()
                key = variation['data-variant-id']

                stock = 0
                qty_input = soup.find('input', {'id': 'input-qty'})
                if qty_input:
                    if qty_input.has_attr('max') and qty_input['max'] != '':
                        stock = int(int(qty_input['max']) / len(variations))
                    else:
                        stock = -1

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
                    description=description,
                    picture_urls=picture_urls
                )
                products.append(p)
            return products
        else:
            key = soup.find('form', 'product-form')['action'].split('/')[-1]

            stock = 0
            qty_input = soup.find('input', 'qty')
            if qty_input:
                if qty_input.has_attr('max') and qty_input['max'] != '':
                    stock = int(qty_input['max'])
                else:
                    stock = -1

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
                description=description,
                picture_urls=picture_urls
            )
            return [p]
