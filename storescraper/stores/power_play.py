from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, CPU_COOLER, \
    EXTERNAL_STORAGE_DRIVE, GAMING_CHAIR, GAMING_DESK, HEADPHONES, KEYBOARD, \
    MEMORY_CARD, MICROPHONE, MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, \
    POWER_SUPPLY, PROCESSOR, RAM, SOLID_STATE_DRIVE, TABLET, \
    USB_FLASH_DRIVE, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PowerPlay(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            SOLID_STATE_DRIVE,
            COMPUTER_CASE,
            POWER_SUPPLY,
            VIDEO_CARD,
            CPU_COOLER,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            EXTERNAL_STORAGE_DRIVE,
            MICROPHONE,
            KEYBOARD,
            MOUSE,
            MONITOR,
            GAMING_DESK,
            GAMING_CHAIR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computadores-tablets/notebook', NOTEBOOK],
            ['computadores-tablets/tablets', TABLET],
            ['componentes-partes-piezas/procesadores', PROCESSOR],
            ['componentes-partes-piezas/placas-madres', MOTHERBOARD],
            ['componentes-partes-piezas/memorias', RAM],
            ['componentes-partes-piezas/almacenamiento-pc', SOLID_STATE_DRIVE],
            ['componentes-partes-piezas/gabinetes-estandar-gamer',
                COMPUTER_CASE],
            ['componentes-partes-piezas/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-partes-piezas/tarjetas-graficas', VIDEO_CARD],
            ['componentes-partes-piezas/refrigeracion', CPU_COOLER],
            ['almacenamiento/pendrive', USB_FLASH_DRIVE],
            ['almacenamiento/microsd-sd', MEMORY_CARD],
            ['almacenamiento/disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
            ['accesorios-perifericos-pc/microfonos', MICROPHONE],
            ['accesorios-perifericos-pc/teclados-estandar-gamer', KEYBOARD],
            ['accesorios-perifericos-pc/mouse-estandar-gamer', MOUSE],
            ['monitores-proyectores', MONITOR],
            ['escritorio-sillas-gamer/escritorios', GAMING_DESK],
            ['escritorio-sillas-gamer/sillas-gamer', GAMING_CHAIR],
            ['audio', HEADPHONES],
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
                url_webpage = 'https://power-play.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                if '404!' in soup.text:
                    break
                product_containers = soup.find(
                    'div', {'id': 'content'}).findAll('li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find(
                        'a', 'woocommerce-LoopProduct-link'
                             ' woocommerce-loop-product__link')['href']
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
            'script', {'type': 'application/ld+json'})[1].text)['@graph'][1]

        name = json_data['name']
        sku = json_data['sku']
        description = json_data['description']

        price = Decimal(json_data['offers'][0]['price'])

        stock = 0
        in_stock = soup.find('p', 'stock in-stock')
        if in_stock:
            stock = int(in_stock.text.split(" ")[0])

        picture_urls = []
        picture_container = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        for i in picture_container.findAll('a'):
            picture_urls.append(i['href'])

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


'''
https://power-play.cl/product-category/computadores-tablets/notebook/
https://power-play.cl/product-category/computadores-tablets/tablets/
https://power-play.cl/product-category/componentes-partes-piezas/procesadores/
https://power-play.cl/product-category/componentes-partes-piezas/placas-madres/
https://power-play.cl/product-category/componentes-partes-piezas/memorias/
https://power-play.cl/product-category/componentes-partes-piezas/almacenamiento-pc/
https://power-play.cl/product-category/componentes-partes-piezas/gabinetes-estandar-gamer/
https://power-play.cl/product-category/componentes-partes-piezas/fuentes-de-poder/
https://power-play.cl/product-category/componentes-partes-piezas/tarjetas-graficas/
https://power-play.cl/product-category/componentes-partes-piezas/refrigeracion/
https://power-play.cl/product-category/almacenamiento/pendrive/
https://power-play.cl/product-category/almacenamiento/microsd-sd/
https://power-play.cl/product-category/almacenamiento/disco-duro-externo/
https://power-play.cl/product-category/accesorios-perifericos-pc/microfonos/
https://power-play.cl/product-category/accesorios-perifericos-pc/teclados-estandar-gamer/
https://power-play.cl/product-category/accesorios-perifericos-pc/mouse-estandar-gamer/
https://power-play.cl/product-category/monitores-proyectores/
https://power-play.cl/product-category/escritorio-sillas-gamer/escritorios/
https://power-play.cl/product-category/escritorio-sillas-gamer/sillas-gamer/
https://power-play.cl/product-category/audio/
'''
