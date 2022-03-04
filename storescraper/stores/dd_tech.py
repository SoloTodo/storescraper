import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class DdTech(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            CPU_COOLER,
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            'Mouse',
            'Keyboard',
            'Monitor',
            'Notebook',
            # 'Printer',
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes/discos-duros-internos', 'StorageDrive'],
            ['componentes/unidades-ssd', 'SolidStateDrive'],
            ['componentes/tarjetas-madre', 'Motherboard'],
            ['componentes/procesadores', 'Processor'],
            ['componentes/disipador-cpu-aire', CPU_COOLER],
            ['componentes/enf-liquidos-aio', CPU_COOLER],
            ['componentes/memoria-ram', 'Ram'],
            ['componentes/tarjetas-de-video', 'VideoCard'],
            ['componentes/fuente-de-alimentacion', 'PowerSupply'],
            ['componentes/gabinetes', 'ComputerCase'],
            ['accesorios/mouse', 'Mouse'],
            ['accesorios/teclado', 'Keyboard'],
            ['monitores/monitores', 'Monitor'],
            ['computadoras/portatiles', 'Notebook'],
            ['impresion/impresoras', 'Printer'],
            ['impresion/multifuncionales', 'Printer'],
            ['celulares/android', 'Cell']
        ]

        base_url = 'https://ddtech.mx/productos/{}?pagina={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                url = base_url.format(url_extension, page)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                products = soup.findAll('div', 'products')

                if not products:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                for product in products:
                    product_url = product.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'name').text

        if not soup.find('a', 'add-cart'):
            return []

        sku = soup.find('a', 'add-cart')['data-product-id']
        stock = int(
            soup.find('div', 'stock-container').find('span', 'value').text)

        price = Decimal(
            soup.find('div', 'price-box').find('span', 'price')
                .text.replace('$', '').replace(',', ''))

        picture_urls = []
        images = soup.findAll('div', 'product-item-holder')

        for image in images:
            picture_urls.append(image.find('a')['href'])

        description = html_to_markdown(
            str(soup.find('div', 'product-tabs')))

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
            'MXN',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=sku
        )

        return [p]
