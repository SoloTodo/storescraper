import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class XtremeTecPc(Store):
    @classmethod
    def categories(cls):
        return [
            # 'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            CPU_COOLER,
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            # 'Ups',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Monitor',
            # 'Headphones',
            'Tablet',
            'Notebook',
            # 'StereoSystem',
            # 'OpticalDiskPlayer',
            # 'Printer',
            # 'MemoryCard',
            'Cell',
            # 'UsbFlashDrive',
            'Television',
            # 'Camera',
            # 'Projector',
            # 'AllInOne',
            'VideoGameConsole'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento/discos-duros/para-pc', 'StorageDrive'],
            ['almacenamiento/discos-duros/para-laptop', 'StorageDrive'],
            ['almacenamiento/discos-duros/ssd', 'SolidStateDrive'],
            ['compo/tarjetas-madre', 'Motherboard'],
            ['compo/procesadores', 'Processor'],
            ['accesorios/ventilacion/disipadores', CPU_COOLER],
            ['compo/memorias-ram', 'Ram'],
            ['compo/tarjetas-de-video', 'VideoCard'],
            ['compo/gabinetes', 'ComputerCase'],
            ['accesorios/teclados-mouse/mouse', 'Mouse'],
            ['accesorios/teclados-mouse/teclados', 'Keyboard'],
            ['accesorios/teclados-mouse/kits', 'KeyboardMouseCombo'],
            ['compo/monitores', 'Monitor'],
            ['equipo/tabletas', 'Tablet'],
            ['equipo/laptops', 'Notebook'],
            ['equipo/laptops-gaming', 'Notebook'],
            ['accesorios/impresion/impresoras', 'Printer'],
            ['multimedia/video/pantallas-y-tv/televisiones', 'Television'],
            ['equipo/all-in-one', 'AllInOne'],
            ['multimedia/diver/consolas-y-video-juegos', 'VideoGameConsole']
        ]

        base_url = 'https://www.xtremetecpc.com/c/{}/'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension)

                if page > 1:
                    url = url + 'page/' + str(page) + '/'

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                print(url)

                response = session.get(url)

                if response.url != url:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                product_container = soup.find('ul', 'products')\

                print(url)
                products = product_container.findAll('li', 'product')

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        response = session.get(url)

        if response.url != url:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'product_title').text
        sku_container = soup.find('span', 'sku')
        if not sku_container:
            return []

        sku = sku_container.text

        if soup.find('p', 'out-of-stock'):
            stock = 0
        else:
            stock = -1

        price_container = soup.find('p', 'price').find('ins')

        if price_container:
            price = price_container.find('span', 'amount').text
        else:
            price = soup.find('p', 'price').find('span', 'amount').text

        price = Decimal(price.replace('$', '').replace(',', ''))

        images = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper').findAll('img')

        picture_urls = [i['src'] for i in images]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

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
        )

        return [p]
