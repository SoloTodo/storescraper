import logging
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR, CPU_COOLER, CELL, NOTEBOOK, \
    ALL_IN_ONE, VIDEO_CARD, PROCESSOR, MONITOR, MOTHERBOARD, RAM, \
    STORAGE_DRIVE, SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, TABLET, \
    EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, MEMORY_CARD, MOUSE, PRINTER, \
    KEYBOARD, HEADPHONES, STEREO_SYSTEM, UPS, TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, \
    session_with_proxy


class Bip(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            VIDEO_CARD,
            PROCESSOR,
            MONITOR,
            MOTHERBOARD,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            CPU_COOLER,
            TABLET,
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            TELEVISION,
            MOUSE,
            PRINTER,
            ALL_IN_ONE,
            KEYBOARD,
            HEADPHONES,
            STEREO_SYSTEM,
            UPS,
            GAMING_CHAIR,
            CELL,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Notebooks
            ['166', NOTEBOOK],
            # All in One
            ['218', ALL_IN_ONE],
            # Tarjetas de video
            ['792', VIDEO_CARD],
            # Proces
            ['784', PROCESSOR],
            # Monitores
            ['761', MONITOR],
            # Placas madre
            ['785', MOTHERBOARD],
            # RAM PC
            ['132', RAM],
            # RAM Notebook
            ['178', RAM],
            # Disco Duro 2,5'
            ['125', STORAGE_DRIVE],
            # Disco Duro 3,5'
            ['124', STORAGE_DRIVE],
            # Disco Duro SSD
            ['413', SOLID_STATE_DRIVE],
            # Fuentes de poder
            ['88', POWER_SUPPLY],
            # Gabinetes
            ['8', COMPUTER_CASE],
            # Gabinetes gamer
            ['707', COMPUTER_CASE],
            # Coolers CPU
            ['5', CPU_COOLER],
            ['790', CPU_COOLER],
            # Tablets
            ['286', TABLET],
            # Discos externos 2.5
            ['128', EXTERNAL_STORAGE_DRIVE],
            # USB Flash
            ['528', USB_FLASH_DRIVE],
            # Memory card
            ['82', MEMORY_CARD],
            # Mouse
            ['20', MOUSE],
            # Mouse Gamer
            ['703', MOUSE],
            # Impresoras
            ['769', PRINTER],
            # Plotter
            ['770', PRINTER],
            # Teclados
            ['12', KEYBOARD],
            # Audífono/Micrófono
            ['70', HEADPHONES],
            # Parlantes
            ['13', STEREO_SYSTEM],
            # UPS
            ['31', UPS],
            # Sillas
            ['591', GAMING_CHAIR],
            ['864', CELL],
            ['762', TELEVISION],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            offset = 0

            while True:
                if offset >= 300:
                    raise Exception('Page overflow: ' + url_extension)

                url_webpage = 'https://bip.cl/categoria/{}/{}'.format(
                    url_extension, offset
                )

                data = session.get(url_webpage, verify=False).text

                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.findAll('div', 'producto')

                if not product_containers:
                    if offset == 0:
                        logging.warning('Empty category: ' + url_webpage)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                offset += 20

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        ajax_session = session_with_proxy(extra_args)
        ajax_session.headers['Content-Type'] = \
            'application/x-www-form-urlencoded; charset=UTF-8'
        response = session.get(url, verify=False)

        if response.status_code in [404, 500]:
            return []

        soup = BeautifulSoup(response.text, 'html5lib')
        name = soup.find('h2', 'title-product').text.strip()
        sku = soup.find('span', 'text-stock').text.strip()
        stocks_container = soup.find('div', 'sucursales-stock')

        if stocks_container and stocks_container.find('i', 'fa-check-circle'):
            stock = -1
        else:
            stock = 0

        price_data = ajax_session.post('https://bip.cl/home/viewProductAjax',
                                       'idProd=' + sku, verify=False).json()
        price = Decimal(price_data['internet_price'].replace('.', ''))

        description = html_to_markdown(
                str(soup.find('div', {'id': 'description'})))

        picture_urls = [tag['src'] for tag in
                        soup.findAll('img', 'primary-img')]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
