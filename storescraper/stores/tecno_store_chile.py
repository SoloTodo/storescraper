import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PRINTER, STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, HEADPHONES, STEREO_SYSTEM, KEYBOARD, MOUSE, \
    GAMING_CHAIR, COMPUTER_CASE, VIDEO_CARD, MOTHERBOARD, RAM, CPU_COOLER, \
    PROCESSOR, MONITOR, NOTEBOOK, POWER_SUPPLY, GAMING_DESK, MICROPHONE, \
    EXTERNAL_STORAGE_DRIVE, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TecnoStoreChile(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            HEADPHONES,
            STEREO_SYSTEM,
            KEYBOARD,
            MOUSE,
            GAMING_CHAIR,
            COMPUTER_CASE,
            MOTHERBOARD,
            RAM,
            CPU_COOLER,
            PROCESSOR,
            MONITOR,
            VIDEO_CARD,
            NOTEBOOK,
            POWER_SUPPLY,
            GAMING_DESK,
            MICROPHONE,
            EXTERNAL_STORAGE_DRIVE,
            CASE_FAN,
            PRINTER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['hardware/almacenamiento/disco-duro-externo',
             EXTERNAL_STORAGE_DRIVE],
            ['hardware/almacenamiento/disco-duro-mecanico', STORAGE_DRIVE],
            ['hardware/almacenamiento/m-2-sata-nvme', SOLID_STATE_DRIVE],
            ['hardware/almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['hardware/fuente-de-poder', POWER_SUPPLY],
            ['hardware/gabinete', COMPUTER_CASE],
            ['hardware/memoria-ram', RAM],
            ['hardware/placa-madre', MOTHERBOARD],
            ['hardware/procesadores', PROCESSOR],
            ['hardware/refrigeracion-por-aire', CPU_COOLER],
            ['hardware/regrigeracion-liquida', CPU_COOLER],
            ['hardware/ventiladores', CASE_FAN],
            ['hardware/tarjeta-de-video', VIDEO_CARD],
            ['monitores', MONITOR],
            ['notebooks', NOTEBOOK],
            ['perifericos/audifonos', HEADPHONES],
            ['perifericos/microfonos', MICROPHONE],
            ['perifericos/mouse', MOUSE],
            ['perifericos/teclados', KEYBOARD],
            ['silla', GAMING_CHAIR],
            ['impresoras', PRINTER],
        ]
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'

        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://tschile.cl/categoria-producto/{}/page' \
                              '/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'ast-grid-common-col')
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
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        description = html_to_markdown(
            str(soup.find('div', 'woocommerce-Tabs-panel--description')))

        if soup.find('form', 'variations_form'):
            name = soup.find('h1', 'product_title').text
            json_variations = json.loads(soup.find('form', 'variations_form')[
                                             'data-product_variations'])
            products = []
            for product in json_variations:
                var_name = name + ' - ' + product['attributes'][
                    'attribute_pa_color']
                sku = str(product['variation_id'])
                stock = product['max_qty']
                normal_price = Decimal(round(product['display_price'] * 1.03))
                offer_price = Decimal(product['display_price'])
                picture_url = [product['image']['url']]
                p = Product(
                    var_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    stock,
                    normal_price,
                    offer_price,
                    'CLP',
                    sku=sku,
                    picture_urls=picture_url
                )
                products.append(p)
            return products
        else:
            json_product = json.loads(
                soup.find('script', {'type': 'application/ld+json'}).text)
            if '@graph' not in json_product:
                return []
            json_product = json_product['@graph'][1]
            name = json_product['name']
            sku = str(json_product['sku'])
            quantity_input = soup.find('input', {'name': 'quantity'})
            if quantity_input and quantity_input['type'] == 'number':
                if quantity_input['max']:
                    stock = int(quantity_input['max'])
                else:
                    stock = -1
            elif quantity_input and quantity_input['type'] == 'hidden':
                stock = 1
            else:
                stock = 0
            normal_price = Decimal(
                round(int(json_product['offers'][0]['price']) * 1.03))
            offer_price = Decimal(json_product['offers'][0]['price'])
            picture_url = [tag['src'] for tag in
                           soup.find('div',
                                     'woocommerce-product-gallery').findAll(
                               'img')]
            p = Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                normal_price,
                offer_price,
                'CLP',
                sku=sku,
                picture_urls=picture_url,
                description=description
            )
            return [p]
