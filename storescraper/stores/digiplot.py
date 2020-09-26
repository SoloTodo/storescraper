import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, \
    session_with_proxy


class Digiplot(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'UsbFlashDrive',
            'Headphones',
            'StereoSystem',
            'PowerSupply',
            'ComputerCase',
            'Printer',
            'Ram',
            'Monitor',
            'Notebook',
            'Motherboard',
            'Processor',
            'CpuCooler',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Ups',
            'VideoCard'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento/disco-duro-externo', 'ExternalStorageDrive'],
            ['almacenamiento/disco-duro-notebook', 'StorageDrive'],
            ['almacenamiento/disco-duro-pc', 'StorageDrive'],
            ['almacenamiento/discos-rigidos-ssd', 'SolidStateDrive'],
            ['almacenamiento/pendrive', 'UsbFlashDrive'],
            ['audio/audifono-alambrico', 'Headphones'],
            ['audio/audifono-bluetooth', 'Headphones'],
            ['audio/parlantes-1.1', 'StereoSystem'],
            ['audio/parlantes-2.0', 'StereoSystem'],
            ['audio/parlantes-2.1', 'StereoSystem'],
            ['gabinetes-y-fuentes/fuente-poder', 'PowerSupply'],
            ['gabinetes-y-fuentes/gabinete-slim', 'ComputerCase'],
            ['gabinetes-y-fuentes/gabinete-vertical', 'ComputerCase'],
            ['impresoras/laser', 'Printer'],
            ['impresoras/multifuncion-laser', 'Printer'],
            ['impresoras/multifuncion-tinta', 'Printer'],
            ['memorias/memoria-gamer-y-grafica', 'Ram'],
            ['memorias/memoria-notebook-%28sodimm%29', 'Ram'],
            ['memorias/memoria-pc-%28udimm%29', 'Ram'],
            ['monitor-y-televisor/monitor-led', 'Monitor'],
            ['notebook-y-tablet/notebook-14"', 'Notebook'],
            ['placa-madre/amd-s-am4', 'Motherboard'],
            ['placa-madre/intel-s-1151', 'Motherboard'],
            ['procesadores/intel-s-1151', 'Processor'],
            ['procesadores/amd-s-am4', 'Processor'],
            ['procesadores/ventilador-cpu', 'CpuCooler'],
            ['teclado-y-mouse/mouse-alambrico', 'Mouse'],
            ['teclado-y-mouse/mouse-bluetooth', 'Mouse'],
            ['teclado-y-mouse/mouse-gamer', 'Mouse'],
            ['teclado-y-mouse/mouse-inalambrico', 'Mouse'],
            ['teclado-y-mouse/teclado', 'Keyboard'],
            ['teclado-y-mouse/teclado-y-mouse', 'KeyboardMouseCombo'],
            ['ups-y-alargador-elec/ups-hasta-900va', 'Ups'],
            ['video/tarjetas-video', 'VideoCard']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 10:
                    raise Exception('Page Overflow')

                url = 'https://www.digiplot.cl/product/category/{}?page={}'\
                    .format(url_extension, page)

                data = session.get(url).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-container')

                if not product_containers:
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        data = re.search(r'value_product = ([\s\S]+?)\];',
                         response.text).groups()[0] + ']'
        data = json.loads(data)[0]

        name = data['descripcion'].strip()
        sku = data['idproducto'].strip()
        stock = round(float(data['stock']))
        # offer_price = Decimal(data['precioweb1'])
        price = Decimal(data['precioweb2'])
        description = None
        if data['long_descrip']:
            description = html_to_markdown(data['long_descrip'])
        picture_urls = [x['href'] for x in soup.findAll('a', 'fancybox')]

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
