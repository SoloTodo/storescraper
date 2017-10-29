import re
from bs4 import BeautifulSoup
from decimal import Decimal

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
            'CpuCooler'
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
            ['105-discos-ssd', 'SolidStateDrive'],
            ['19-fuentes-de-poder', 'PowerSupply'],
            ['16-gabinetes', 'ComputerCase'],
            ['53-refrigeracion', 'CpuCooler'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            category_url = 'http://www.mybox.cl/' + category_path + '?n=50'

            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            prod_list = soup.find('ul', {'id': 'product_list'})

            if not prod_list:
                raise Exception('Empty category: ' + category_url)

            prod_cells = prod_list.findAll('li')

            if not prod_cells:
                raise Exception('Empty category: ' + category_url)

            for cell in prod_cells:
                product_urls.append(cell.find('a')['href'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text

        stock = int(re.search(r'quantityAvailable=(-?\d+)',
                              page_source).groups()[0])

        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1').text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value'].strip()

        price = soup.find('span', {'id': 'our_price_display'}).string
        price = Decimal(remove_words(price))

        description = html_to_markdown(
            str(soup.find('div', {'id': 'idTab1'})))

        picture_urls = [soup.find('div',
                                  {'id': 'image-block'}).find('img')['src']]

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
