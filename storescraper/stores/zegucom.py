import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Zegucom(Store):
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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['sub=SAT', 'StorageDrive'],
            ['sub=DNS', 'StorageDrive'],
            ['sub=SSD', 'SolidStateDrive'],
            ['fam=TM', 'Motherboard'],
            ['fam=PR', 'Processor'],
            ['sub=DIS', CPU_COOLER],
            ['sub=ENF', CPU_COOLER],
            ['sub=DR3', 'Ram'],
            ['sub=DR4', 'Ram'],
            ['sub=LD3', 'Ram'],
            ['sub=LD4', 'Ram'],
            # ['sub=PPC', 'VideoCard'],
            ['sub=PCI', 'VideoCard'],
            ['sub=FP', 'PowerSupply'],
            ['sub=GC', 'ComputerCase'],
            ['sub=OP', 'Mouse'],
            ['sub=TE', 'Keyboard'],
            ['sub=TI', 'Keyboard'],
            ['sub=TCO', 'KeyboardMouseCombo'],
            ['sub=TCI', 'KeyboardMouseCombo'],
            ['sub=LED', 'Monitor'],
            ['sub=TAB', 'Tablet'],
            ['sub=NT', 'Notebook'],
            ['sub=IY', 'Printer'],
            ['sub=LS', 'Printer'],
            ['sub=MFI', 'Printer'],
            ['sub=MFL', 'Printer'],
            ['sub=SMP', 'Cell'],
            ['sub=TLED', 'Television'],
            ['sub=AIO', 'AllInOne'],
        ]

        base_url = 'https://www.zegucom.com.mx/index.php?' \
                   'mod=search&{}&sp={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 0

            while True:
                url = base_url.format(url_extension, page)
                print(url)

                if page >= 20:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_container = soup.find('div', 'search-results')
                if not product_container or not \
                        product_container.findAll('div', 'result-description'):
                    if page == 0:
                        logging.warning('Empty category: ' + url_extension)
                    break
                products = product_container.findAll(
                    'div', 'result-description')

                for product in products:
                    product_urls.append('https://www.zegucom.com.mx{}'.format(
                        product.find('a')['href']))

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        well = soup.find('div', 'well')
        if well and 'no disponible' in well.text:
            return []

        if not soup.find('div', 'item-description'):
            return []

        name = soup.find('div', 'item-description').text.strip()

        if len(name) > 256:
            name = name[0:256]

        sku = None
        part_number = None
        stock = 0

        data_block = soup.findAll('div', 'item-tech-info')

        for data_row in data_block:
            data_row_contents = data_row.findAll('div', 'col-flex')
            for data_col in data_row_contents:
                data_pair = data_col.text.strip().split(':')
                if data_pair[0] == 'UPC':
                    sku = data_pair[1].strip()
                if data_pair[0] == 'Núm. de parte':
                    part_number = data_pair[1].strip()
                if data_pair[0] == 'Disponibilidad':
                    stock = int(data_pair[1].strip().split(' ')[0])

        price_tags = soup.findAll('span', 'price-text')
        prices = []

        for price_tag in price_tags:
            price_text = re.search(r'\$(\d*,?\d+\.?\d*)',
                                   price_tag.text).groups()[0]
            prices.append(Decimal(price_text.replace(',', '')))

        price = min(prices)

        if soup.find('img', 'larger2'):
            picture_urls = ['https://www.zegucom.com.mx/{}'.format(
                soup.find('img', 'larger2')['src'])]
        else:
            picture_urls = []

        description = html_to_markdown(
            str(soup.find('div', {'id': 'ficha'})))

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
            part_number=part_number
        )

        return [p]
