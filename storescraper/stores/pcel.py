import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Pcel(Store):
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
            'Mouse',
            'Keyboard',
            'Monitor',
            'Tablet',
            'Notebook',
            # 'Printer',
            'Cell',
            'Television',
            # 'AllInOne',
            'VideoGameConsole'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['hardware/discos-duros/discos-duros-internos', 'StorageDrive'],
            ['hardware/discos-duros/unidades-de-estado-solido-ssd',
             'SolidStateDrive'],
            ['hardware/tarjetas-madre', 'Motherboard'],
            ['hardware/procesadores', 'Processor'],
            ['hardware/disipadores-y-ventiladores', CPU_COOLER],
            ['hardware/memorias/memorias-ddr', 'Ram'],
            ['hardware/memorias/memoria-sodimm-laptops', 'Ram'],
            ['hardware/tarjetas-de-video', 'VideoCard'],
            ['hardware/fuentes-de-poder', 'PowerSupply'],
            ['hardware/gabinetes', 'ComputerCase'],
            ['accesorios/mouse-ratones', 'Mouse'],
            ['accesorios/teclados', 'Keyboard'],
            ['hardware/monitores', 'Monitor'],
            ['computadoras/tablets', 'Tablet'],
            ['computadoras/ipad', 'Tablet'],
            ['computadoras/laptops', 'Notebook'],
            ['hardware/impresoras', 'Printer'],
            ['electronica/telefonia/smartphones', 'Cell'],
            ['electronica/televisores', 'Television'],
            ['electronica/videojuegos/consolas', 'VideoGameConsole']
        ]

        base_url = 'https://www.pcel.com/{}?page={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)

                if page >= 30:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                products = soup.findAll('a', 'productClick')

                if not products:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                for product in products:
                    product_urls.append(product['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'product-pcel').text.strip()
        data = soup.find('div', 'description').contents
        data_container = [
            d for d in data if str(d) not in ["\n", " ", "<br/>"]]

        sku = None
        part_number = None

        for index, data in enumerate(data_container):
            if "Sku:" in data:
                sku = data_container[index+1].strip()
            if "Modelo:" in data:
                if "Envío" not in str(data_container[index+1]):
                    part_number = data_container[index+1].strip()

        price = Decimal(
            soup.find('td', {'data-description': 'price'})['data-price']
                .replace('$', '').replace(',', ''))

        picture_urls = []
        images = soup.findAll('img', 'cloudzoom')

        for image in images:
            picture_url = 'https:{}'.format(image['src'])\
                .replace('/300/', '/1600/')
            picture_urls.append(picture_url)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        stock_source = session.get(
            'https://pcel.com/index.php?route=pcel/stock&sku={}'
            .format(sku)).text
        stock_soup = BeautifulSoup(stock_source, 'html.parser')
        table_trs = stock_soup.findAll('tr')[1:]
        stock = 0

        for tr in table_trs:
            tds = tr.findAll('td')
            if tds[0].text == "Bajo Pedido" or tds[1].text == '\n**':
                continue
            stock += int(tr.findAll('td')[1].text)

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
