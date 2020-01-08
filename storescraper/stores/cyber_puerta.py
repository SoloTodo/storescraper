import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class CyberPuerta(Store):
    @classmethod
    def categories(cls):
        return [
            # 'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            'CpuCooler',
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
            'Printer',
            # 'MemoryCard',
            'Cell',
            # 'UsbFlashDrive',
            'Television',
            # 'Camera',
            # 'Projector',
            'AllInOne',
            'VideoGameConsole'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['Computo-Hardware/Discos-Duros-SSD-NAS/Discos-Duros-Externos',
             'ExternalStorageDrive'],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/'
             'Discos-Duros-Internos-para-PC', 'StorageDrive'],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/Discos-Duros-para-NAS',
             'StorageDrive'],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/'
             'Discos-Duros-Internos-para-Laptop', 'StorageDrive'],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/'
             'Discos-Duros-para-Videovigilancia', 'StorageDrive'],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/SSD',
             'StorageDrive'],
            ['Computo-Hardware/Componentes/Tarjetas-Madre', 'MotherBoard'],
            ['Computo-Hardware/Componentes/Procesadores/Procesadores-para-PC',
             'Processor'],
            ['Computo-Hardware/Componentes/Enfriamiento-Ventilacion/'
             'Disipadores-para-CPU', 'CpuCooler'],
            ['Computo-Hardware/Componentes/Enfriamiento-Ventilacion/'
             'Refrigeracion-Liquida', 'CpuCooler'],
            ['Computo-Hardware/Memorias-RAM-Flash/Memorias-RAM-para-PC',
             'Ram'],
            ['Computo-Hardware/Memorias-RAM-Flash/Memorias-RAM-para-Laptop',
             'Ram'],
            ['Computo-Hardware/Memorias-RAM-Flash/Memorias-RAM-para-Mac',
             'Ram'],
            ['Computo-Hardware/Componentes/Tarjetas-de-Video', 'VideoCard'],
            ['Computo-Hardware/Componentes/Fuentes-de-Poder-para-PC-s',
             'PowerSupply'],
            ['Computo-Hardware/Componentes/Gabinetes', 'ComputerCase'],
            ['Computo-Hardware/Dispositivos-de-entrada/Mouse', 'Mouse'],
            ['Computo-Hardware/Dispositivos-de-entrada/Teclados', 'Keyboard'],
            ['Computo-Hardware/Dispositivos-de-entrada/'
             'Kits-de-Teclado-y-Mouse', 'KeyboardMouseCombo'],
            ['Computo-Hardware/Monitores/Monitores', 'Monitor'],
            ['Computadoras/Tabletas/Tabletas', 'Tablet'],
            ['Computadoras/Laptops', 'Notebook'],
            ['Impresion-Copiado/Impresoras-Multifuncionales/Impresoras',
             'Printer'],
            ['Impresion-Copiado/Impresoras-Multifuncionales/'
             'Impresoras-Fotograficas', 'Printer'],
            ['Impresion-Copiado/Impresoras-Multifuncionales/Multifuncionales',
             'Printer'],
            ['Telecomunicacion/Telefonia-Movil/Smartphones', 'Cell'],
            ['Audio-Video/TV-Pantallas/Pantallas-LED/', 'Television'],
            ['Computadoras/All-in-One', 'AllInOne'],
            ['Audio-Video/Consolas-Juegos/Nintendo-Switch/'
             'Consolas-Nintendo-Switch', 'VideoGameConsole'],
            ['Audio-Video/Consolas-Juegos/Xbox-One/Consolas-Xbox-One',
             'VideoGameConsole'],
            ['Audio-Video/Consolas-Juegos/Nintendo', 'VideoGameConsole'],
            ['Audio-Video/Consolas-Juegos/Playstation-4-PS4/'
             'Consolas-Playstation-4', 'VideoGameConsole'],
            ['Audio-Video/Consolas-Juegos/Nintendo-2DS/Consolas-Nintendo-2DS',
             'VideoGameConsole']
        ]

        base_url = 'https://www.cyberpuerta.mx/{}/'
        filter = 'Filtro/Estatus/En-existencia'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension)
                if page > 1:
                    url = url + str(page) + '/'
                url = url + filter

                if page >= 100:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_container = soup.find('ul', {'id': 'productList'})\

                if not product_container:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                products = product_container.findAll('li', 'productData')

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'detailsInfo_right_title').text
        sku = soup.find('div', 'detailsInfo_right_artnum')\
            .text.replace('SKU:', '').strip()

        if not soup.find('span', 'stockFlag'):
            stock = 0
        else:
            stock = int(soup.find('span', 'stockFlag').find('span').text)

        price = Decimal(soup.find('span', 'priceText').text.replace('$', '').replace(',', ''))

        picture_urls = []
        images = soup.find('div', 'emslider2_items').findAll('li')

        for image in images:
            picture_urls.append(image.find('a')['data-src'])

        description = html_to_markdown(
            str(soup.find('div', 'cpattributes-box')))

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
            part_number=sku
        )

        return [p]
