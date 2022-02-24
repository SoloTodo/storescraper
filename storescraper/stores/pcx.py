import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Pcx(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            CPU_COOLER,
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            'Mouse',
            'Keyboard',
            'KeboardMouseCombo',
            'Monitor',
            'Notebook',
            # 'Printer',
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['18-discos-duros', 'StorageDrive'],
            ['29-ssd', 'SolidStateDrive'],
            ['20-tarjetas-madre', 'Motherboard'],
            ['4-procesadores', 'Proccessor'],
            ['7-disipadores-por-aire-para-cpu', CPU_COOLER],
            ['80-memoria-ram', 'Ram'],
            ['21-tarjetas-de-video', 'VideoCard'],
            ['15-fuentes-de-poder', 'PowerSupply'],
            ['16-gabinetes', 'ComputerCase'],
            ['25-mouse', 'Mouse'],
            ['32-teclados', 'Keyboard'],
            ['68-kits-de-teclado-y-mouse', 'KeyboardMouseCombo'],
            ['70-monitores-led', 'Monitor'],
            ['71-notebooks', 'Notebook'],
            ['136-impresoras', 'Printer'],
            ['202-multifuncionales', 'Printer']
        ]

        base_url = 'https://www.pcx.com.mx/{}?p={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                url = base_url.format(url_extension, page)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('li', 'ajax_block_product')

                for product_container in product_containers:
                    product_url = product_container.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('span', {'itemprop': 'productID'}).text

        if soup.find('div', {'id': 'disponible'}):
            stock = -1
        else:
            stock = 0

        price = Decimal(
            soup.find('span', {'id': 'our_price_display'})
                .text.replace(',', '').replace('$', ''))

        picture_urls = [soup.find('img', 'clear bigpic')['src']]

        description = html_to_markdown(str(soup.find('div', {'id': 'idTab1'})))

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
        )

        return [p]
