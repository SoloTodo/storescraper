import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, COMPUTER_CASE, MOTHERBOARD, \
    USB_FLASH_DRIVE, CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class IsiBook(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Tablet',
            'Printer',
            'StereoSystem',
            'StorageDrive',
            'ExternalStorageDrive'
            'UsbFlashDrive',
            'MemoryCard',
            'SolidStateDrive',
            'Projector',
            'Monitor',
            'AllInOne',
            'Mouse',
            'Keyboard',
            'Headphones',
            'Processor',
            'PowerSupply',
            'Ram',
            'VideoCard',
            GAMING_CHAIR,
            COMPUTER_CASE,
            MOTHERBOARD,
            CPU_COOLER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['pc-y-portatiles/all-in-one', 'AllInOne'],
            ['pc-y-portatiles/notebook', 'Notebook'],
            ['pc-y-portatiles/tablet', 'Tablet'],
            ['audio-video-y-fotografia/audifonos', 'Headphones'],
            ['audio-video-y-fotografia/parlantes', 'StereoSystem'],
            ['partes-y-piezas/tarjeta-de-video', 'VideoCard'],
            ['partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/monitores', 'Monitor'],
            ['partes-y-piezas/placas-madre', MOTHERBOARD],
            ['partes-y-piezas/procesadores', 'Processor'],
            ['partes-y-piezas/fuentes-de-poder', 'PowerSupply'],
            ['partes-y-piezas/memorias-ram', 'Ram'],
            ['partes-y-piezas/refrigeracion', CPU_COOLER],
            ['almacenamiento/disco-duros', 'StorageDrive'],
            ['almacenamiento/pendrives-y-memorias-flash', USB_FLASH_DRIVE],
            ['impresion/multifuncionales-tinta', 'Printer'],
            ['impresion/impresoras-laser', 'Printer'],
            ['accesorios/sillas', GAMING_CHAIR],
            ['accesorios/mouse-teclado-y-mousepad', 'Mouse'],
            ['gamers', 'Motherboard'],
        ]

        session = session_with_proxy(extra_args)
        base_url = 'https://www.isibook.cl/{}.html?product_list_limit=64&p={}'
        product_urls = []

        for url_extension, local_category in category_paths:
            if category != local_category:
                continue

            page = 1
            local_urls = []
            done = False

            while not done:
                if page > 10:
                    raise Exception('Page overflow')

                url = base_url.format(url_extension, page)
                print(url)
                res = session.get(url)
                if res.url != url:
                    raise Exception('URL mismatch: ' + url + ' ' + res.url)
                soup = BeautifulSoup(res.text, 'html.parser')
                product_containers = soup.find('ol', 'products')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty path: ' + url)
                    break

                products = product_containers.findAll('li', 'item')

                for product in products:
                    product_url = product.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break
                    local_urls.append(product_url)

                page += 1

            product_urls.extend(local_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code in [410, 404]:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('span', 'sku').text.split(':')[1].strip()
        stock = 0

        if soup.find('button', {'id': 'product-addtocart-button'}):
            stock = -1

        offer_price = Decimal(
            soup.find('span', 'special-price').find('span', 'price')
                .text.replace('$', '').replace('.', ''))
        normal_price = Decimal(
            soup.find('span', 'price-credit-card')
                .text.replace('$', '').replace('.', ''))

        picture_urls = [soup.find('div', 'preloaded-image').find('img')['src']]

        description = html_to_markdown(
            str(soup.find('div', 'description')))

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
            description=description,
        )

        return [p]
