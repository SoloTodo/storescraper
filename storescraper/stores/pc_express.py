import re
from bs4 import BeautifulSoup
from decimal import Decimal

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
            'PowerSupply',
            'ComputerCase',
            'CpuCooler',
            'Tablet',
            'MemoryCard',
            'UsbFlashDrive',
            'ExternalStorageDrive',
            'Printer',
            'Television',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_info = [
            ['61', 'Processor'],
            ['61_169', 'CpuCooler'],  # Ventilacion para CPU
            ['60', 'Motherboard'],
            ['62_101', 'StorageDrive'],  # HDD Desktop
            ['62_103', 'StorageDrive'],  # HDD Notebook
            ['62_102', 'ExternalStorageDrive'],  # HDD Externo
            ['62_331', 'SolidStateDrive'],
            ['62_106', 'MemoryCard'],
            ['62_107', 'UsbFlashDrive'],
            ['70_118', 'PowerSupply'],  # Fuentes de poder basicas
            ['70_279', 'PowerSupply'],  # Fuentes de poder reales
            ['70_119', 'ComputerCase'],  # Gabinetes basicos
            ['70_120', 'ComputerCase'],  # Gabinetes gamer
            ['70_278', 'ComputerCase'],  # Gabinetes slim
            ['71', 'Printer'],
            ['72', 'Ram'],
            ['73_171', 'Monitor'],
            # ['73_129', 'Television'],
            ['74_133', 'Mouse'],
            ['313_319', 'Mouse'],
            ['75_136', 'Notebook'],
            ['75_223', 'Tablet'],
            # ['241_269', 'Tablet'],
            ['83', 'VideoCard'],
            ['135', 'Keyboard'],
            ['313_318', 'Keyboard'],
            ['131', 'KeyboardMouseCombo'],
            ['64_146', 'Headphones'],   # Audifonos
            ['321', 'Headphones'],   # Audifonos Gamers
            ['353', 'Headphones'],   # Audífonos Micrófono Bluetooth
            ['64_282', 'Headphones'],   # Audifonos Microfono
            ['147', 'StereoSystem'],   # Parlantes
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_id, local_category in category_info:
            if local_category != category:
                continue

            category_url = 'https://tienda.pc-express.cl/index.php?route=' \
                           'product/category&path=' + category_id + '&page='
            page = 1

            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + category_id)
                category_page_url = category_url + str(page)
                soup = BeautifulSoup(session.get(category_page_url).text,
                                     'html.parser')
                td_products = soup.findAll('div', 'product-list__image')

                if len(td_products) == 0:
                    if page == 1:
                        raise Exception('Empty category: ' + category_id)
                    break

                else:
                    for td_product in td_products:
                        original_product_url = td_product.find(
                            'a')['href']

                        product_id = re.search(r'product_id=(\d+)',
                                               original_product_url
                                               ).groups()[0]
                        product_url = 'https://tienda.pc-express.cl/' \
                                      'index.php?route=product/product&' \
                                      'product_id=' + product_id
                        product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'rm-product-page__title').text
        sku = soup.find('p', 'rm-product__code').span.text

        availability_table = soup.find('div', 'rm-product__stock')
        stock = 0

        if availability_table is not None:
            availability_table = availability_table.ul
            availability_cells = availability_table.findAll('li')

            for cell in availability_cells:
                cell_text = cell.span.text.lower().strip()

                if 'más de 20 unidades' == cell_text:
                    stock = -1
                    break

                stock_match = re.match(r'(\d+) unidad', cell_text)

                if stock_match:
                    stock += int(stock_match.groups()[0])

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
            picture_urls=picture_urls
        )

        return [p]
