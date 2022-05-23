import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CPU_COOLER, STEREO_SYSTEM, COMPUTER_CASE, \
    GAMING_CHAIR, TABLET, NOTEBOOK, WEARABLE, VIDEO_CARD, POWER_SUPPLY, RAM, \
    MOTHERBOARD, PROCESSOR, HEADPHONES, KEYBOARD_MOUSE_COMBO, MEMORY_CARD, \
    EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    USB_FLASH_DRIVE, MONITOR, PRINTER, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TecnoSite(Store):
    @classmethod
    def categories(cls):
        return [
            TABLET,
            NOTEBOOK,
            ALL_IN_ONE,
            WEARABLE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            STEREO_SYSTEM,
            MEMORY_CARD,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            MONITOR,
            PRINTER,
            CPU_COOLER,
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gamer/refrigeracion', CPU_COOLER],
            ['gamer/audio', STEREO_SYSTEM],
            ['gamer/gabinetes', COMPUTER_CASE],
            ['gamer/sillas', GAMING_CHAIR],
            ['tablets-en-oferta', TABLET],
            ['portatiles/notebooks', NOTEBOOK],
            ['pc-escritorio/all-in-one', ALL_IN_ONE],
            ['smartwatch-chile/smartwatch', WEARABLE],
            ['componentes/bundles', VIDEO_CARD],
            ['componentes/fuentes', POWER_SUPPLY],
            ['componentes/gabinete', COMPUTER_CASE],
            ['componentes/memorias', RAM],
            ['componentes/placas-madre', MOTHERBOARD],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['accesorios/audifonos', HEADPHONES],
            ['accesorios/kit-tecl', KEYBOARD_MOUSE_COMBO],
            ['accesorios/parlantes', STEREO_SYSTEM],
            ['accesorios/perifericos', KEYBOARD_MOUSE_COMBO],
            ['almacenamiento/memoria-sd', MEMORY_CARD],
            ['almacenamiento/disco-externo', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento/hdd', STORAGE_DRIVE],
            ['almacenamiento/ssd-m-2', SOLID_STATE_DRIVE],
            ['almacenamiento/pendrive-usb', USB_FLASH_DRIVE],
            ['monitores-y-pantallas', MONITOR],
            ['impresion-e-imagen', PRINTER],
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

                url_webpage = 'https://tienda.tecno-site.com/product-' \
                              'category/{}/page/{}/'.format(url_extension,
                                                            page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

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

        if not soup.find('span', {'id': 'final-price'}):
            return []

        name = soup.find('h1', 'product_title').text.strip()[:256]
        part_number_tag = soup.find('span', 'sku')

        if part_number_tag:
            part_number = part_number_tag.text
        else:
            part_number = None

        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]

        stock_tag = soup.find('input', {'name': 'quantity'})
        if stock_tag:
            if 'max' in stock_tag.attrs:
                if stock_tag['max']:
                    stock = int(stock_tag['max'])
                else:
                    stock = -1
            else:
                stock = 1
        else:
            stock = 0

        price = Decimal(
            soup.find('span', {'id': 'final-price'}).text.replace('.', ''))
        picture_urls = [tag['src'] for tag in soup.find('div', 'woocommerce'
                                                               '-product-'
                                                               'gallery').
                        findAll('img') if 'No-Disponible' not in tag['src']]
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
            'CLP',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
