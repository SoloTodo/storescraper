import json
import re
import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown


class Wei(Store):
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
            'Lamp',
            'LightTube',
            'LightProjector',
            'Mouse',
            'Printer',
            'VideoGameConsole',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_urls = [
            ['1267', 'Notebook'],  # Notebooks
            ['1264', 'Notebook'],  # Notebooks ultralivianos
            ['731', 'Notebook'],  # NOTEBOOK GAMER
            ['1257', 'Mouse'],  # Mouse
            ['1138', 'ExternalStorageDrive'],  # Discos externos
            ['665', 'ExternalStorageDrive'],  # Discos externos FORMATO 2.5"
            ['664', 'ExternalStorageDrive'],  # Discos externos FORMATO 3.5"
            ['515', 'SolidStateDrive'],  # SSD
            ['1141', 'MemoryCard'],  # Tarjetas de memoria
            ['511', 'StorageDrive'],  # HDD PC SATA
            ['513', 'StorageDrive'],  # HDD Notebook SATA
            ['1142', 'UsbFlashDrive'],  # Pendrive
            ['1127', 'Motherboard'],  # AM3
            ['1128', 'Motherboard'],  # AM3+
            ['668', 'Motherboard'],  # FM2+
            ['660', 'Motherboard'],  # 1150
            ['687', 'Motherboard'],  # 1151
            ['1131', 'Motherboard'],  # 1155
            ['1133', 'Motherboard'],  # 2011
            ['730', 'Motherboard'],  # PLACAS GAMER
            ['1162', 'CpuCooler'],  # Ventilacion
            ['673', 'Processor'],  # AM1
            ['602', 'Processor'],  # FM2
            ['674', 'Processor'],  # FM2+
            ['1119', 'Processor'],  # AM3+
            ['657', 'Processor'],  # 1150
            ['691', 'Processor'],  # 1151
            ['1125', 'Processor'],  # 2011
            ['1220', 'ComputerCase'],  # Gabinetes c/ PSU
            ['1221', 'ComputerCase'],  # Gabinetes s/ PSU
            ['729', 'ComputerCase'],  # GABINETES GAMER
            ['1239', 'Ram'],  # RAM PC
            ['1241', 'Ram'],  # RAM Notebook
            ['1240', 'Ram'],  # MEMORIA PC GAMER
            ['1222', 'PowerSupply'],  # Fuentes de poder
            ['1307', 'VideoCard'],  # Tarjetas de video AMD
            ['1306', 'VideoCard'],  # Tarjetas de video NVIDIA
            ['1209', 'VideoGameConsole'],  # Consolas
            ['635', 'Lamp'],  # FOCOS LED
            ['630', 'LightTube'],  # TUBOS LED
            ['627', 'Lamp'],  # AMPOLLETAS LED
            ['628', 'Lamp'],  # DICROICOS LED
            ['636', 'LightProjector'],  # PROYECTORES DE AREA LED
            ['1228', 'Printer'],  # IMPRESORA TINTA
            ['1227', 'Printer'],  # Impresoras Laser
            ['715', 'Printer'],  # MULTIFUNCIONALES LASER
            ['1231', 'Printer'],  # MULTIFUNCIONALES TINTA
            ['1234', 'Printer'],  # PLOTTER
            ['1245', 'Monitor'],  # MONITORES LED, LCD, TFT
            ['1248', 'Television'],  # TELEVISORES LCDTV
            ['678', 'Tablet'],  # Tablets
            # ['638', 'LightTube'],  # TUBOS LED
            # ['676', 'Motherboard'],   # AM1
            # ['719', 'Processor'],   # CPU AMD AM4 CON PLACA MADRE Y COOLER
        ]

        session = requests.Session()

        product_urls = []
        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 0

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + category_path)

                page_url = 'https://www.wei.cl/categoria/{}?page={}' \
                           ''.format(category_path, page)

                soup = BeautifulSoup(session.get(page_url).text, 'html.parser')

                product_cells = soup.findAll('div', 'box-producto')

                if not product_cells:
                    if page == 0:
                        raise Exception('Empty category: {}'.format(
                            category_path))
                    break

                for cell in product_cells:
                    product_url = cell.find('a')['href']
                    if product_url in product_urls:
                        continue
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = requests.Session()

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        pricing_str = re.search('retailrocket.products.post\((.+)\);',
                                page_source).groups()[0]
        pricing_json = json.loads(pricing_str)

        name = pricing_json['name']
        if pricing_json['isAvailable']:
            stock = -1
        else:
            stock = 0

        sku = pricing_json['url'].split('/')[-1]
        offer_price = Decimal(pricing_json['price'])

        normal_price = soup.findAll(
            'div', 'pb10')[2].contents[0].split('$')[1]
        normal_price = Decimal(remove_words(normal_price))

        description = html_to_markdown(str(soup.find(
            'div', {'id': 'tab-producto'})))

        picture_urls = []
        for picture_container in soup.findAll('div', 'slider-item'):
            picture_url = picture_container.find('img')['src']
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
