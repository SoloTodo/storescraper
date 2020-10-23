import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, RAM, MEMORY_CARD, \
    MONITOR, MOUSE, KEYBOARD, KEYBOARD_MOUSE_COMBO, MOTHERBOARD, PROCESSOR, \
    CPU_COOLER, VIDEO_CARD, STEREO_SYSTEM, HEADPHONES


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
            RAM, MEMORY_CARD,
            MONITOR,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD,
            STEREO_SYSTEM,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['40', STORAGE_DRIVE],  # Discos duros notebook
            ['41', SOLID_STATE_DRIVE],  # SSD
            ['42', EXTERNAL_STORAGE_DRIVE],  # Discos duros extenos
            ['86', STORAGE_DRIVE],  # Discos duros NAS
            ['87', SOLID_STATE_DRIVE],  # SSD M.2
            ['87', STORAGE_DRIVE],  # Discos duros 3.5"
            ['88', POWER_SUPPLY],  # Fuentes de poder ATX
            ['89', POWER_SUPPLY],  # Fuentes de poder modulares
            ['90', COMPUTER_CASE],  # Gabinetes Micro ATX
            ['91', COMPUTER_CASE],  # Gabinetes ATX-E
            ['44', RAM],  # RAM Desktop
            ['45', RAM],  # RAM Notebook
            ['46', MEMORY_CARD],  # Tarjetas de memoria
            ['27', MONITOR],  # Monitores y proyectores
            ['47', MOUSE],  # Mouses
            ['48', KEYBOARD],  # Teclados
            ['49', KEYBOARD_MOUSE_COMBO],  # Kits
            ['54', MOTHERBOARD],  # Placas madre sTR4
            ['55', MOTHERBOARD],  # Placas madre AM4
            ['56', MOTHERBOARD],  # Placas madre AM3+
            ['57', MOTHERBOARD],  # Placas madre FM2
            ['58', MOTHERBOARD],  # Placas madre 1151
            ['59', MOTHERBOARD],  # Placas madre 2066
            ['97', MOTHERBOARD],  # Placas madre 1200
            ['60', PROCESSOR],  # Procesadores AM4
            ['61', PROCESSOR],  # Procesadores sTR4
            ['62', PROCESSOR],  # Procesadores AM3+
            ['63', PROCESSOR],  # Procesadores FM2
            ['64', PROCESSOR],  # Procesadores 2066
            ['65', PROCESSOR],  # Procesadores 1151
            ['98', PROCESSOR],  # Procesadores 1200
            ['74', CPU_COOLER],  # Cooler Procesador
            ['77', VIDEO_CARD],  # Tarjetas de video NVIDIA
            ['78', VIDEO_CARD],  # Tarjetas de video Profesionales
            ['99', VIDEO_CARD],  # Tarjetas de video AMD
            ['94', STEREO_SYSTEM],  # Parlantes
            ['95', HEADPHONES],  # Audífonos
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

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(
                    category_url, timeout=30).text, 'html5lib')

                product_cells = soup\
                    .find('section', 'product_show_list')\
                    .findAll('article', 'product-miniature')

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
        name = soup.find('h1', 'product_name').text.strip()
        sku = soup.find('span', {'itemprop': 'sku'}).text.strip()
        price_tags = soup.findAll('span', {'itemprop': 'price'})
        offer_price = Decimal(price_tags[0]['content'])
        normal_price = Decimal(price_tags[1]['content'])

        availability_message = soup.find(
            'span', {'id': 'product-availability'}).contents[2].strip()

        if availability_message in ['Producto sin Stock, solo reservas.',
                                    'Producto fuera de stock.']:
            stock = 0
        else:
            stock = int(soup.find(
                'div', 'product-quantities').find('span')['data-stock'])

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))
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
