import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class MyBox(Store):
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
            'Keyboard',
            'Mouse',
            'KeyboardMouseCombo',
            'Ups',
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # ['38-notebooks', 'Notebook'],
            ['7-monitores-y-proyectores', 'Monitor'],
            ['41-placas-madre', 'Motherboard'],
            ['44-procesadores', 'Processor'],
            ['54-tarjetas-de-video', 'VideoCard'],
            ['28-memoria-ram', 'Ram'],
            ['5-discos-duros', 'StorageDrive'],
            ['126-tarjeta-m2-ssd', 'SolidStateDrive'],
            ['19-fuentes-de-poder', 'PowerSupply'],
            ['16-gabinetes', 'ComputerCase'],
            ['53-refrigeracion', 'CpuCooler'],
            ['77-teclado-keyboard', 'Keyboard'],
            ['55-teclado-y-mouse', 'Mouse'],
            ['57-ups', 'Ups'],
            ['133-sillas-gamer-gaming-chair', GAMING_CHAIR]
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.54.0'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            category_url = 'https://www.mybox.cl/' + category_path + '?n=50'

            print(category_url)

            soup = BeautifulSoup(session.get(category_url, timeout=30).text,
                                 'html.parser')
            prod_list = soup.find('ul', {'id': 'product_list'})

            if not prod_list:
                raise Exception('Empty category: ' + category_url)

            prod_cells = prod_list.findAll('li')

            if not prod_cells:
                raise Exception('Empty category: ' + category_url)

            for cell in prod_cells:
                product_urls.append(
                    cell.find('a')['href'].replace('http:', 'https:'))

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.54.0'
        page_source = session.get(url, timeout=30).text

        stock = int(re.search(r"quantityAvailable=(-?\d+)",
                              page_source).groups()[0])

        if stock > 0:
            stock = -1
        else:
            stock = 0

        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1').text.strip()
        sku = re.search(r"id_product='(\d+)'", page_source).groups()[0]

        price = re.search(r"productPriceTaxExcluded=(\d+)",
                          page_source).groups()[0]
        price = Decimal(price)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'idTab1'})))

        picture_urls = [x['href'] for x in soup.findAll('a', 'thickbox')]

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
