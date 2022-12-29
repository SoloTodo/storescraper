from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import *
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MyShop(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            STEREO_SYSTEM,
            MONITOR,
            TELEVISION,
            CELL,
            WEARABLE,
            NOTEBOOK,
            ALL_IN_ONE,
            TABLET,
            USB_FLASH_DRIVE,
            PRINTER,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            COMPUTER_CASE,
            CPU_COOLER,
            POWER_SUPPLY,
            MOUSE,
            GAMING_CHAIR,
            MICROPHONE,
            VIDEO_GAME_CONSOLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audio-y-video/audifonos-in-ear', HEADPHONES],
            ['audio-y-video/audifonos-on-ear', HEADPHONES],
            ['audio-y-video/parlantes', STEREO_SYSTEM],
            ['audio-y-video/monitores', MONITOR],
            ['audio-y-video/televisores', TELEVISION],
            ['tecnologia-movil/celulares', CELL],
            ['tecnologia-movil/relojes', WEARABLE],
            ['computacion/notebooks', NOTEBOOK],
            ['computacion/all-in-one', ALL_IN_ONE],
            ['computacion/tablet', TABLET],
            ['computacion/almacenamiento-externo', USB_FLASH_DRIVE],
            ['computacion/impresion-laser', PRINTER],
            ['computacion/impresion-tinta', PRINTER],
            ['partes-y-piezas/procesadores', PROCESSOR],
            ['partes-y-piezas/placas-madres', MOTHERBOARD],
            ['partes-y-piezas/memorias-ram', RAM],
            ['partes-y-piezas/almacenamiento', SOLID_STATE_DRIVE],
            ['partes-y-piezas/tarjetas-de-video', VIDEO_CARD],
            ['partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/refrigeracion', CPU_COOLER],
            ['partes-y-piezas/fuentes-de-poder', POWER_SUPPLY],
            ['partes-y-piezas/teclados-y-mouse', MOUSE],
            ['gamer/notebooks-gamer', NOTEBOOK],
            ['gamer/audifonos-gamer', HEADPHONES],
            ['gamer/teclados-y-mouse-gamer', MOUSE],
            ['gamer/sillas-y-mesas', GAMING_CHAIR],
            ['gamer/microfonos', MICROPHONE],
            ['entretencion/consolas', VIDEO_GAME_CONSOLE],
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
                url_webpage = 'https://www.myshop.cl/categorias/{}'\
                              '/page/{}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                collection = soup.find('div', 'products')
                if not collection:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                product_containers = collection.findAll('div', 'product')
                for container in product_containers:
                    product_url = container.find(
                        'h3', 'product-title').find('a')['href']
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

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)
        for entry in json_data['@graph']:
            if '@type' in entry and entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        sku = product_data['sku']
        description = product_data['description']
        price = Decimal(product_data['offers'][0]['price'])

        stock_p = soup.find('p', 'stock in-stock')
        if stock_p:
            if 'más de' in stock_p.text.lower():
                stock = -1
            else:
                stock = int(stock_p.text.split(' ')[0])
        else:
            stock = 0

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
            description=description
        )
        return [p]