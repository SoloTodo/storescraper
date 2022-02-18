import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words
from storescraper.categories import STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, RAM, MEMORY_CARD, \
    MONITOR, MOUSE, KEYBOARD, KEYBOARD_MOUSE_COMBO, MOTHERBOARD, PROCESSOR, \
    CPU_COOLER, VIDEO_CARD, STEREO_SYSTEM, HEADPHONES, GAMING_CHAIR, \
    USB_FLASH_DRIVE, PRINTER, CASE_FAN


class TtChile(Store):
    preferred_products_for_url_concurrency = 3

    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD,
            STEREO_SYSTEM,
            HEADPHONES,
            GAMING_CHAIR,
            USB_FLASH_DRIVE,
            PRINTER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['37', VIDEO_CARD],  # Tarjetas de video
            ['33', PROCESSOR],  # Procesadores AMD
            ['34', PROCESSOR],  # Procesadores Intel
            ['31', MOTHERBOARD],  # Placas madre AMD
            ['32', MOTHERBOARD],  # Placas madre Intel
            ['113', STORAGE_DRIVE],  # HDD
            ['114', SOLID_STATE_DRIVE],  # SSD
            ['44', RAM],  # DDR4
            ['45', RAM],  # RAM Notebook
            ['46', USB_FLASH_DRIVE],  # Flash / USB
            ['79', POWER_SUPPLY],  # Fuentes de poder
            ['74', CPU_COOLER],  # Cooler Procesador
            ['76', CPU_COOLER],  # Refrigeración Líquida
            ['82', COMPUTER_CASE],  # Gabinetes
            ['27', MONITOR],  # Monitores y proyectores
            ['47', MOUSE],  # Mouses
            ['48', KEYBOARD],  # Teclados
            ['49', KEYBOARD_MOUSE_COMBO],  # Kits
            ['94', STEREO_SYSTEM],  # Parlantes
            ['95', HEADPHONES],  # Audífonos
            ['107', PRINTER],  # Impresoras
            ['100', GAMING_CHAIR],  # Sillas y Escritorio
            ['42', EXTERNAL_STORAGE_DRIVE],  # Discos duros extenos
            ['73', CASE_FAN],  # Ventiladores
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.tytchilespa.cl/Home/index.php?' \
                               'id_category={}&controller=category&page={}' \
                               ''.format(category_path, page)
                print(category_url)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(
                    category_url, timeout=30).text, 'html5lib')
                product_list_tag = soup.find('section', 'product_show_list')

                if not product_list_tag:
                    if page == 1:
                        logging.warning('Empty category: ' + category_url)
                    break

                product_cells = product_list_tag.findAll(
                    'article', 'product-miniature')

                if not product_cells:
                    if page == 1:
                        logging.warning('Empty category: ' + category_url)
                    break

                for product_cell in product_cells:
                    product_url = product_cell.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        soup = BeautifulSoup(session.get(
            url, timeout=30).text, 'html.parser')

        sku_tag = soup.find('span', {'itemprop': 'sku'})

        if not sku_tag:
            return []

        sku = sku_tag.text.strip()
        name = soup.find('h1', 'product_name').text.strip()

        base_price = Decimal(
            soup.find('meta', {'property': 'product:price:amount'})['content'])
        assert soup.find('meta', {'property': 'product:price:currency'})[
                   'content'] == 'CLP'
        offer_price = (base_price * Decimal('0.95')).quantize(0)
        normal_price = (base_price * Decimal('1.03')).quantize(0)

        availability_message = soup.find(
            'span', {'id': 'product-availability'}).contents[2].strip()

        if availability_message in ['Producto sin Stock, solo reservas.',
                                    'Producto fuera de stock.']:
            stock = 0
        else:
            quantities_tag = soup.find('div', 'product-quantities')
            if quantities_tag:
                stock = int(quantities_tag.find('span')['data-stock'])
            else:
                stock = -1

        description = html_to_markdown(
            str(soup.find('div', 'tab-content')))
        picture_urls = [x['data-image-large-src'] for x in
                        soup.find('ul', 'product-images').findAll('img')]

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
            picture_urls=picture_urls
        )

        return [p]
