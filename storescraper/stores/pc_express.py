import logging
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class PcExpress(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'VideoCard',
            'Processor',
            'Monitor',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'PowerSupply',
            'ComputerCase',
            'CpuCooler',
            'Tablet',
            'MemoryCard',
            'UsbFlashDrive',
            'Printer',
            'Television',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'StereoSystem',
            'Ups',
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_info = [
            ['136', 'Notebook'],              # Comercial y corporativos
            ['475', 'VideoCard'],             # Tarjetas de Video
            ['473', 'Processor'],             # Procesadores
            ['73_523_171', 'Monitor'],        # Monitores Tradicionales
            ['73_523_128', 'Monitor'],        # Monitores Gamer
            ['73_523_129', 'Monitor'],        # Monitores Profesionales
            ['472', 'Motherboard'],           # Placas Madres
            ['72', 'Ram'],                    # Memorias
            ['101', 'StorageDrive'],          # Discos Duros para PC
            ['103', 'StorageDrive'],          # Discos Duros para Notebook
            ['411', 'StorageDrive'],          # Discos Duros para NAS
            ['412', 'StorageDrive'],          # Discos Duros para vigilancia
            ['331', 'SolidStateDrive'],       # Unidades de estado Solido
            ['102', 'ExternalStorageDrive'],  # Discod Duros Externos
            ['118', 'PowerSupply'],           # Fuentes Estandar
            ['279', 'PowerSupply'],           # Fuentes Certificadas
            ['460_462_119', 'ComputerCase'],  # Gabinetes Basicos
            ['460_462_120', 'ComputerCase'],  # Gabinetes Gamer
            ['460_462_278', 'ComputerCase'],  # Gabinetes SLIM
            ['169', 'CpuCooler'],             # Ventilacion para CPU
            ['269', 'Tablet'],                # Tablets
            ['106', 'MemoryCard'],            # Memorias Flash
            ['107', 'UsbFlashDrive'],         # Pendrive
            ['493', 'Printer'],               # Impresoras Hogar y Oficina
            ['460_466_471', 'Mouse'],         # Mouse Gamers
            ['460_466_470', 'Keyboard'],      # Teclados Gamers
            ['460_466_467', 'KeyboardMouseCombo'],  # Combos Teclado y Mouse
            ['321', 'Headphones'],            # Audifonos Gamers
            ['282', 'Headphones'],            # Audifonos Microfono Bluetooth
            ['282', 'Headphones'],            # Microfonos y Manos Libres
            ['427', 'StereoSystem'],          # Parlantes/Subwoofer/Soundbar
            ['154', 'Ups'],                    # Ups
            ['313_576', GAMING_CHAIR]
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'

        for category_id, local_category in category_info:
            if local_category != category:
                continue

            category_url = 'https://tienda.pc-express.cl/index.php?route=' \
                           'product/category&path=' + category_id + '&page='
            page = 1

            while True:
                if page > 15:
                    raise Exception('Page overflow: ' + category_id)

                category_page_url = category_url + str(page)
                soup = BeautifulSoup(
                    session.get(category_page_url).text, 'html.parser')
                td_products = soup.findAll('div', 'product-list__image')

                if len(td_products) == 0:
                    if page == 1:
                        logging.warning('Empty category: ' + category_id)
                    break

                else:
                    for td_product in td_products:
                        original_product_url = td_product.find('a')['href']

                        product_id = re.search(
                            r'product_id=(\d+)',
                            original_product_url).groups()[0]

                        product_url = 'https://tienda.pc-express.cl/' \
                                      'index.php?route=product/product&' \
                                      'product_id=' + product_id

                        product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'rm-product-page__title').text
        sku = soup.find('div', 'rm-product__id').h3.text
        if not soup.find('p', 'rm-product__mpn'):
            part_number = None
        else:
            part_number = soup.find(
                'p', 'rm-product__mpn').text.split(':')[-1].strip()

        stock_container = soup.find('div', 'rm-producto-stock-message')

        if not stock_container:
            stock = 0
        elif stock_container.text == 'Sin disponibilidad para venta web':
            stock = 0
        else:
            stock = int(stock_container.text.split(' ')[0])

        offer_price = soup.find('div', 'rm-product__price--cash').h3.text
        offer_price = Decimal(remove_words(offer_price))

        normal_price = soup.find('div', 'rm-product__price--normal').h3.text
        normal_price = Decimal(remove_words(normal_price))

        description = html_to_markdown(str(soup.find(
            'div', {'id': 'tab-description'})))

        picture_urls = None

        thumbnails = soup.find('ul', 'thumbnails')

        if thumbnails:
            picture_urls = [thumbnails.a['href']]

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
            description=description,
            picture_urls=picture_urls,
            part_number=part_number
        )

        return [p]
