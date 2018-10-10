import html
import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


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
            'Keyboard',
            'KeyboardMouseCombo',
            'AllInOne',
            'Headphones',
            'Projector',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_urls = [
            ['752', 'Tablet'],  # Tablets
            ['678', 'Tablet'],  # TABLETS
            ['1267', 'Notebook'],  # Notebooks
            ['731', 'Notebook'],  # NOTEBOOK GAMER
            ['1252', 'Mouse'],  # Mouse
            ['732', 'Mouse'],  # ACCESORIOS GAMER
            ['1138', 'ExternalStorageDrive'],  # Discos externos
            ['515', 'SolidStateDrive'],  # SSD
            ['1142', 'UsbFlashDrive'],  # Pendrive
            ['511', 'StorageDrive'],  # DISCOS DUROS INTERNOS
            ['769', 'AllInOne'],  # ALL IN ONE - AIO
            ['770', 'Headphones'],  # AUDIFONOS CON MICROFONO
            ['1176', 'Headphones'],  # AUDíFONOS
            ['1126', 'Motherboard'],  # PLACAS MADRES
            ['1219', 'ComputerCase'],  # GABINETES
            ['729', 'ComputerCase'],  # GABINETES GAMER
            ['1222', 'PowerSupply'],  # FUENTES DE PODER (PSU)
            ['1305', 'VideoCard'],  # TARJETAS DE VIDEO
            ['1117', 'Processor'],  # Procesadores
            ['1238', 'Ram'],  # MEMORIAS
            ['1162', 'CpuCooler'],  # VENTILADORES / FAN
            ['1267', 'Notebook'],  # NOTEBOOKS
            ['784', 'Printer'],  # IMPRESORA TINTA
            ['773', 'Printer'],  # IMPRESORAS LASER
            ['775', 'Printer'],  # IMPRESORAS MULTIFUNCIONALES
            ['1226', 'Printer'],  # IMPRESORAS TINTA
            ['1249', 'Projector'],  # PROYECTORES
            ['1245', 'Monitor'],  # MONITORES LED, LCD, TFT
            ['1248', 'Television'],  # TELEVISORES
            ['1295', 'Cell'],  # SMARTPHONES
            ['1141', 'MemoryCard'],  # Tarjetas de memoria
            ['1254', 'Keyboard'],  # TECLADOS (PS2, USB, NUMERICOS)
            ['1253', 'KeyboardMouseCombo'],  # COMBOS TECLADO / MOUSE
            ['1175', 'StereoSystem'],  # PARLANTES
            ['793', 'StereoSystem'],  # AMPLIFICADORES
        ]

        session = session_with_proxy(extra_args)

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
                print(page_url)

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
        session = session_with_proxy(extra_args)

        page_source = session.get(url, verify=False).text
        soup = BeautifulSoup(page_source, 'html.parser')

        pricing_str = re.search('retailrocket.products.post\((.+)\);',
                                page_source)

        if not pricing_str:
            return []

        pricing_json = json.loads(pricing_str.groups()[0])

        name = html.unescape(pricing_json['name'])

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
            picture_url = picture_container.find('img')['src'].replace(
                ' ', '%20')
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
