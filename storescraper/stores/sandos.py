import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, HEADPHONES, MOUSE, KEYBOARD, \
    GAMING_CHAIR, MONITOR, MOTHERBOARD, RAM, POWER_SUPPLY, CPU_COOLER, \
    COMPUTER_CASE, PROCESSOR, SOLID_STATE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Sandos(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_CARD,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            GAMING_CHAIR,
            MONITOR,
            MOTHERBOARD,
            RAM,
            POWER_SUPPLY,
            CPU_COOLER,
            COMPUTER_CASE,
            PROCESSOR,
            SOLID_STATE_DRIVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['monitores', MONITOR],
            ['componentes/almacenamiento', SOLID_STATE_DRIVE],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['componentes/placas-madre', MOTHERBOARD],
            ['componentes/memorias-ram', RAM],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/cooler', CPU_COOLER],
            ['componentes/gabinetes', COMPUTER_CASE],
            ['accesorios/audifonos', HEADPHONES],
            ['accesorios/mouse', MOUSE],
            ['accesorios/teclados', KEYBOARD],
            ['sillas-gamer', GAMING_CHAIR],
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
                url_webpage = 'https://sandos.cl/product-category' \
                              '/{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                if soup.find('body', 'error404'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                script_tag = soup.find('script', {'type': 'text/template'})

                if not script_tag:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                soup = BeautifulSoup(json.loads(script_tag.text),
                                     'html.parser')

                product_containers = soup.findAll('li', 'product-col')

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
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
            -1]
        soup = BeautifulSoup(
            json.loads(soup.find('script', {'type': 'text/template'}).text),
            'html.parser')

        name = soup.find('h2').text.strip()
        if soup.find('form', 'variations_form'):

            variations = json.loads(soup.find('form', 'variations_form')[
                                        'data-product_variations'])
            products = []
            for variation in variations:
                variation_name = name + ' - ' + variation['attributes'][
                    'attribute_pa_color']
                sku = str(variation['variation_id'])
                if variation['is_in_stock']:
                    stock = variation['max_qty']
                else:
                    stock = 0
                price = Decimal(variation['display_price'])
                picture_urls = [variation['image']['url']]
                p = Product(
                    variation_name,
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

            if soup.find('span', 'product-stock'):
                stock = int(soup.find('span', 'product-stock').find('span',
                                                                    'stock').
                            text.split()[0])
            else:
                stock = -1
            if soup.find('p', 'price').find('ins'):
                price = Decimal(
                    remove_words(soup.find('p', 'price').find('ins').text))
            else:
                price = Decimal(remove_words(soup.find('p', 'price').text))
            picture_urls = [tag['src'] for tag in
                            soup.find('div', 'product-images').findAll('img')]
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
