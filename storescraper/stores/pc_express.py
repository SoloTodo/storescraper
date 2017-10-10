import re
import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown


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
            ['73_129', 'Television'],
            ['74_133', 'Mouse'],
            ['75_136', 'Notebook'],
            ['75_223', 'Tablet'],
            ['241_269', 'Tablet'],
            ['83', 'VideoCard'],
        ]

        product_urls = []
        session = requests.Session()

        for category_id, local_category in category_info:
            if local_category != category:
                continue

            category_url = 'http://www.pc-express.cl/index.php?cPath=' + \
                           category_id + '&page='

            page = 1
            local_product_urls = []

            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + category_id)

                category_page_url = category_url + str(page)
                soup = BeautifulSoup(session.get(category_page_url).text,
                                     'html.parser')
                td_products = soup.findAll('div', 'box-product')
                break_flag = False

                for td_product in td_products:
                    original_product_url = td_product.find(
                        'a', 'image-wrapper')['href']
                    product_id = re.search(r'products_id=(\d+)',
                                           original_product_url).groups()[0]
                    product_url = 'http://www.pc-express.cl/' \
                                  'product_info.php?products_id=' + product_id

                    if product_url in local_product_urls:
                        break_flag = True
                        break
                    local_product_urls.append(product_url)

                if break_flag:
                    if page == 1:
                        raise Exception('Empty category: ' + category_id)
                    break

                page += 1

            product_urls.extend(local_product_urls)

        return list(set(product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = requests.Session()
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text
        sku = soup.find('input', {'name': 'products_id'})['value'].strip()

        availability_table = soup.find(
            'div', 'description-box').nextSibling.nextSibling

        availability_cells = availability_table.findAll('td', 'text-right')

        stock = 0

        for cell in availability_cells:
            cell_text = cell.text.lower()

            if cell_text.encode('utf-8') == \
                    b'm\xc3\xa3\xc2\xa1s de 20 unidades':
                stock = -1
                break

            stock_match = re.match(r'(\d+) unidades', cell_text)

            if stock_match:
                stock += int(stock_match.groups()[0])

        offer_price = soup.findAll('span', 'product-price-number')[1]
        offer_price = Decimal(remove_words(offer_price.text))

        normal_price = soup.findAll('span', 'product-price-number')[0]
        normal_price = Decimal(remove_words(normal_price.text))

        description = html_to_markdown(str(soup.find('div', 'description')))

        picture_urls = ['http://www.pc-express.cl/' +
                        soup.find('a', 'product-image')['href']]

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
