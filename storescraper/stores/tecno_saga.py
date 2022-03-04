import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, HEADPHONES, POWER_SUPPLY, COMPUTER_CASE, MOTHERBOARD, \
    CPU_COOLER, GAMING_CHAIR, VIDEO_CARD, PRINTER, RAM, USB_FLASH_DRIVE, \
    MEMORY_CARD, MONITOR, MOUSE, STEREO_SYSTEM, KEYBOARD, PROCESSOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TecnoSaga(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            HEADPHONES,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            GAMING_CHAIR,
            VIDEO_CARD,
            PRINTER,
            MEMORY_CARD,
            RAM,
            USB_FLASH_DRIVE,
            MONITOR,
            MOUSE,
            STEREO_SYSTEM,
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['discos-duro-interno-48-4', STORAGE_DRIVE],
            ['discos-duro-notebook-49-4', STORAGE_DRIVE],
            ['disco-duro-externo-50-4', EXTERNAL_STORAGE_DRIVE],
            ['unidad-de-estado-solido-ssd-51-4', SOLID_STATE_DRIVE],
            ['audio-video-2', HEADPHONES],
            ['fuentes-de-poder-reales-52-8', POWER_SUPPLY],
            ['fuente-poder-generica-53-8', POWER_SUPPLY],
            ['gabinetes-basicos-54-8', COMPUTER_CASE],
            ['gabinetes-gamer-55-8', COMPUTER_CASE],
            ['placas-madres-amd-63-8', MOTHERBOARD],
            ['placas-madres-intel-64-8', MOTHERBOARD],
            ['procesadores-amd-66-8', PROCESSOR],
            ['procesadores-intel-67-8', PROCESSOR],
            ['refrigeracion-ventiladores-68-8', CPU_COOLER],
            ['sillas-gamer-escritorios-gamer-69-8', GAMING_CHAIR],
            ['tarjetas-de-video-91-8', VIDEO_CARD],
            ['impresoras-scaners-9', PRINTER],
            ['memoria-flash-71-10', MEMORY_CARD],
            ['memoria-ram-notebook-72-10', RAM],
            ['memoria-ram-pc-73-10', RAM],
            ['pendrive-74-10', USB_FLASH_DRIVE],
            ['monitores-11', MONITOR],
            ['teclados-mouse-82-12', MOUSE],
            ['parlantes-83-12', STEREO_SYSTEM],
            ['teclados-90-12', KEYBOARD]
        ]

        session = session_with_proxy(extra_args)
        session.headers['x-requested-with'] = 'XMLHttpRequest'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)

                url_webpage = 'https://tecnosaga.cl/productos/listadoajax'
                categories = url_extension.split('-')
                body = {'mostrar': 16, 'id_categoria': categories[-1],
                        'id_subcategoria': categories[-2], 'pagina': page}
                data = json.loads(session.post(url_webpage, data=body).text)
                product_containers = data['productos']
                if not product_containers:
                    logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = 'https://tecnosaga.cl/productos/detalle/' + \
                                  container['url']
                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.url == 'https://tecnosaga.cl/':
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h4', 'product_title').text
        sku_container = soup.find('div', 'cart_btn').find('button',
                                                          'btn')['onclick']
        sku = re.search(r'agregar_producto\((\d+)\)', sku_container).groups()[
            0]
        stock = 0
        for products_stock in soup.find('div', 'pr_detail'). \
                findAll('div', 'col-lg-3'):
            if products_stock.text.strip().split()[-1].isnumeric():
                stock += int(products_stock.text.strip().split()[-1])

        normal_price = Decimal(soup.find('ul', 'product-meta producto-tarjeta')
                               .text.strip().split()[1].replace('.', ''))
        offer_price = Decimal(soup.find('ul', 'product-meta producto-normal')
                              .text.strip().split()[1].replace('.', ''))
        if normal_price < offer_price:
            offer_price = normal_price
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'col-lg-6').findAll('img')]
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
            picture_urls=picture_urls,
        )
        return [p]
