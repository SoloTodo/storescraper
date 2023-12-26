import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, MOTHERBOARD, \
    PROCESSOR, RAM, STORAGE_DRIVE, SOLID_STATE_DRIVE, EXTERNAL_STORAGE_DRIVE, \
    HEADPHONES, MOUSE, MONITOR, KEYBOARD, CPU_COOLER, \
    VIDEO_CARD, GAMING_CHAIR, NOTEBOOK, POWER_SUPPLY, \
    CASE_FAN, STEREO_SYSTEM, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class ETChile(StoreWithUrlExtensions):
    url_extensions = [
        # ['componentes-partes-y-piezas/almacenamiento/discos-duros', STORAGE_DRIVE],
        ['componentes-partes-y-piezas/almacenamiento/ssd', SOLID_STATE_DRIVE],
        ['componentes-partes-y-piezas/gabinetes', COMPUTER_CASE],
        ['componentes-partes-y-piezas/memorias', RAM],
        ['componentes-partes-y-piezas/placas-madres', MOTHERBOARD],
        ['componentes-partes-y-piezas/procesadores', PROCESSOR],
        ['componentes-partes-y-piezas/psu-fuentes-de-poder', POWER_SUPPLY],
        ['componentes-partes-y-piezas/refrigeracion/ventiladores',
         CASE_FAN],
        ['componentes-partes-y-piezas/refrigeracion/water-cooling',
         CPU_COOLER],
        ['componentes-partes-y-piezas/tarjetas-de-video', VIDEO_CARD],
        ['perifericos/audio-y-streaming/audifonos', HEADPHONES],
        ['perifericos/audio-y-streaming/parlantes-y-equipo-de-sonido', STEREO_SYSTEM],
        ['perifericos/mouse-accesorios/mouse', MOUSE],
        ['perifericos/teclados/teclados-mecanicos', KEYBOARD],
        ['productos/almacenamiento-y-drives/discos-externos',
         EXTERNAL_STORAGE_DRIVE],
        ['productos/almacenamiento-y-drives/hdd-interno', STORAGE_DRIVE],
        ['productos/almacenamiento-y-drives/memorias-flash', STORAGE_DRIVE],
        ['productos/almacenamiento-y-drives/ssd-externo', EXTERNAL_STORAGE_DRIVE],
        ['productos/almacenamiento-y-drives/ssd-interno-almacenamiento-y-drives', SOLID_STATE_DRIVE],
        ['productos/consolas-y-vr', VIDEO_GAME_CONSOLE],
        ['productos/monitores/monitores-gamer', MONITOR],
        ['productos/notebooks/notebooks-gamers', NOTEBOOK],
        ['productos/sillas-y-escritorios/sillas', GAMING_CHAIR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://etchile.net/categorias/{}/'.format(url_extension)
            if page > 1:
                url_webpage += 'page/{}/'.format(page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('div', 'product-small')

            if not product_containers:
                if page == 1:
                    logging.warning('Emtpy category: ' + url_extension)
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
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text.strip()
        if soup.find('form', 'variations_form'):
            product_variations = json.loads(
                soup.find('form', 'variations_form')[
                    'data-product_variations'])
            products = []
            for variation in product_variations:
                variation_name = name + ' - ' + variation['attributes'][
                    'attribute_color']
                sku = variation['sku']
                key = str(variation['variation_id'])
                stock = variation['max_qty']
                price = Decimal(variation['display_price']).quantize(0)
                picture_urls = [variation['image']['url']]

                p = Product(
                    variation_name,
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
                    part_number=sku,
                    picture_urls=picture_urls,
                )
                products.append(p)
            return products

        else:
            sku = None
            if soup.find('span', 'sku'):
                sku = soup.find('span', 'sku').text
            key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                -1]

            stock_tag = soup.find('input', {'name': 'quantity'})
            if stock_tag:
                if 'max' in stock_tag.attrs:
                    if '' == stock_tag['max']:
                        stock = -1
                    else:
                        stock = int(stock_tag['max'])
                else:
                    stock = 1
            else:
                stock = 0

            if soup.find('p', 'price').find('ins'):
                price = Decimal(
                    remove_words(
                        soup.find('p', 'price').find('ins').text.strip()))
            else:
                price = Decimal(
                    remove_words(soup.find('p', 'price').text.strip()))

            picture_urls = [tag.find('img')['data-src'].split('?')[0] for tag
                            in
                            soup.findAll('li', 'product_thumbnail_item')]
            description = html_to_markdown(
                str(soup.find('div', 'woocommerce-Tabs-panel--description')))
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
                part_number=sku,
                picture_urls=picture_urls,
                description=description
            )
            return [p]
