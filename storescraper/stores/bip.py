import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Bip(Store):
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
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Television',
            'Mouse'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://www.bip.cl/ecommerce/'
        url_buscar_productos = 'index_2.php?modulo=busca&'

        url_extensions = [
            # Netbooks
            ['categoria=167&categoria_papa=166', 'Notebook'],
            # Tarjetas de video
            ['categoria=118&categoria_papa=97', 'VideoCard'],
            # Proces
            ['categoria=111', 'Processor'],
            # LCD
            ['categoria=19', 'Monitor'],
            # Placas madre
            ['categoria=108', 'Motherboard'],
            # RAM PC
            ['categoria=132', 'Ram'],
            # RAM Notebook
            ['categoria=178', 'Ram'],
            # RAM Servidor
            ['categoria=179', 'Ram'],
            # Disco Duro 2,5'
            ['categoria=125&categoria_papa=123', 'StorageDrive'],
            # Disco Duro 3,5'
            ['categoria=124&categoria_papa=123', 'StorageDrive'],
            # Disco Duro SSD
            ['categoria=413&categoria_papa=123', 'SolidStateDrive'],
            # Fuentes de poder
            ['categoria=88&categoria_papa=114', 'PowerSupply'],
            # Gabinetes
            ['categoria=8&categoria_papa=114', 'ComputerCase'],
            # Coolers CPU
            ['categoria=5&categoria_papa=248', 'CpuCooler'],
            # Tablets
            ['categoria=421&categoria_papa=286', 'Tablet'],
            # Discos externos
            ['categoria=230&categoria_papa=123', 'ExternalStorageDrive'],
            # USB Flash
            ['categoria=145&categoria_papa=123', 'UsbFlashDrive'],
            # Memory card
            ['categoria=82&categoria_papa=24', 'MemoryCard'],
            # Mouse
            ['categoria=20&categoria_papa=185', 'Mouse'],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 0

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + url_extension)

                url_webpage = url_base + url_buscar_productos + url_extension \
                    + '&pagina=' + str(page)

                print(url_webpage)

                data = session.get(url_webpage).text

                soup = BeautifulSoup(data, 'html.parser')
                raw_links = soup.findAll('a', 'menuprod')[::2]

                if not raw_links:
                    if page == 0:
                        raise Exception('Empty category: ' + url_webpage)
                    break

                for raw_link in raw_links:
                    product_urls.append(url_base + raw_link['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('td', 'menuprodg').find('h1').text.strip()
        sku = soup.find('input', {'name': 'id_producto'})['value']

        stock_source = soup.find('input', {'name': 'COMPRAR'})['onclick']
        stock = int(re.search(r'var x=(\d+);', stock_source).groups()[0])

        if stock == 0:
            stock_info = soup.find('td', 'disp')
            stock_string = ''.join(str(stock) for stock in stock_info.contents)
            if 'Agotado' not in stock_string and \
                    'Producto a Pedido' not in stock_string:
                stock = -1

        inet_price_cell = soup.find('td', 'prcm')
        offer_price = Decimal(remove_words(inet_price_cell.string))

        normal_price_cell = soup.findAll('td', 'prc8')[1]
        normal_price = Decimal(remove_words(normal_price_cell.string))

        description = ''

        description_container = soup.find('table', 'brd')
        if description_container:
            description = html_to_markdown(
                str(description_container.find('td')))

        picture_urls = []
        for picture_link in soup.find('td', 'bdyzoom').findAll('a'):
            picture_url = 'https://www.bip.cl' + picture_link['href']
            picture_urls.append(picture_url)

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
