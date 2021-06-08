import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import NOTEBOOK, ALL_IN_ONE, TABLET, \
    STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, SOLID_STATE_DRIVE, MEMORY_CARD, \
    USB_FLASH_DRIVE, PROCESSOR, COMPUTER_CASE, POWER_SUPPLY, MOTHERBOARD, \
    RAM, VIDEO_CARD, MOUSE, PRINTER, HEADPHONES, STEREO_SYSTEM, UPS, MONITOR, \
    KEYBOARD_MOUSE_COMBO, KEYBOARD, PROJECTOR


class Cintegral(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            ALL_IN_ONE,
            TABLET,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            PROCESSOR,
            COMPUTER_CASE,
            POWER_SUPPLY,
            MOTHERBOARD,
            RAM,
            VIDEO_CARD,
            MOUSE,
            PRINTER,
            HEADPHONES,
            STEREO_SYSTEM,
            UPS,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            KEYBOARD,
            PROJECTOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://www.cintegral.cl/index.php?' \
                   'id_category={}&controller=category&page={}'

        url_extensions = [
            ['24', NOTEBOOK],  # Notebooks
            ['25', ALL_IN_ONE],  # All in One
            ['27', TABLET],  # Tablet
            ['66', STORAGE_DRIVE],  # Discos duros PC
            ['67', EXTERNAL_STORAGE_DRIVE],  # Discos duros externos
            ['68', SOLID_STATE_DRIVE],  # Unidades de estado sólido
            ['69', MEMORY_CARD],  # Memorias Flash
            ['70', USB_FLASH_DRIVE],  # Pendrive
            ['31', PROCESSOR],  # Procesadores
            ['32', COMPUTER_CASE],  # Gabinetes
            ['33', POWER_SUPPLY],  # Fuentes de poder
            ['34', MOTHERBOARD],  # Placas madre
            ['71', RAM],  # Memorias PC
            ['72', RAM],  # Memorias Notebook
            ['36', VIDEO_CARD],  # Tarjetas de video
            ['39', KEYBOARD_MOUSE_COMBO],  # Combos teclado mouse
            ['40', MOUSE],  # Mouse
            ['38', KEYBOARD],  # Teclados
            ['45', PRINTER],  # Impresoras tinta
            ['46', PRINTER],  # Impresoras láser
            ['47', PRINTER],  # Multifuncionales tinta
            ['48', PRINTER],  # Multifuncionales láser
            ['59', HEADPHONES],  # Audífonos / Micrófonos
            ['60', STEREO_SYSTEM],  # Parlantes
            ['61', UPS],  # UPS
            ['18', MONITOR],  # Monitores
            ['56', PROJECTOR],  # Proyectores
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + url_extension)

                url = url_base.format(url_extension, page)
                source = session.get(url, verify=False).text
                soup = BeautifulSoup(source, 'html.parser')

                products = soup.find('div', 'products row')

                if not products:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                containers = soup.find('div', 'products row') \
                    .findAll('a', 'product-thumbnail')

                for product_link in containers:
                    product_url = product_link['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url, verify=False).text
        soup = BeautifulSoup(page_source, 'html.parser')
        name = soup.find('h1', 'product-detail-title').text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value']

        part_number = None
        part_number_container = soup.find('span', {'itemprop': 'sku'})
        if part_number_container:
            part_number = part_number_container.text.strip()

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

        add_to_cart_button = soup.find('button', 'add-to-cart')

        if 'disabled' in add_to_cart_button.attrs:
            stock = 0
        else:
            stock = -1

        price = Decimal(soup.find('div', 'current-price')
                        .find('span', {'itemprop': 'price'})['content'])

        pictures = soup.find('ul', 'product-images').findAll('img')
        picture_urls = [p['data-image-large-src'] for p in pictures]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
