import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, HEADPHONES, STEREO_SYSTEM, KEYBOARD, MOUSE, \
    GAMING_CHAIR, COMPUTER_CASE, \
    VIDEO_CARD, MOTHERBOARD, RAM, CPU_COOLER, PROCESSOR, MONITOR, NOTEBOOK, \
    POWER_SUPPLY
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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios/audifonos-clasicos', HEADPHONES],
            ['accesorios/mouse-de-escrtorio', MOUSE],
            ['accesorios/parlantes-y-equipos-de-audio', STEREO_SYSTEM],
            ['gamer/perifericos/audifono', HEADPHONES],
            ['gamer/perifericos/teclados', KEYBOARD],
            ['gamer/perifericos/mouse', MOUSE],
            ['notebooks', NOTEBOOK],
            ['hardware/procesadores', PROCESSOR],
            ['hardware/almacenamiento/hdd-disco-duro', STORAGE_DRIVE],
            ['hardware/almacenamiento/ssd-unidad-de-estado-solido',
             SOLID_STATE_DRIVE],
            ['hardware/almacenamiento/m-2-sata-y-nvme', SOLID_STATE_DRIVE],
            ['hardware/fuente-de-poder', POWER_SUPPLY],
            ['hardware/gabinetes', COMPUTER_CASE],
            ['hardware/gpu', VIDEO_CARD],
            ['hardware/memoria-ram', RAM],
            ['hardware/placa-madre', MOTHERBOARD],
            ['hardware/refrigeracion-y-ventilacion', CPU_COOLER],
            ['monitores', MONITOR],
            ['sillas', GAMING_CHAIR],
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
        response = session.get(url)
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
                normal_price = Decimal(round(product['display_price'] * 1.05))
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
            stock_tag = soup.find('span', 'stock in-stock')
            if stock_tag:
                stock = int(stock_tag.text.split()[0])
            else:
                stock = -1
            normal_price = Decimal(
                round(int(json_product['offers'][0]['price']) * 1.05))
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
