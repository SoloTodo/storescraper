import re

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class SpDigital(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Tablet',
            'Notebook',
            'StereoSystem',
            'OpticalDiskPlayer',
            'PowerSupply',
            'ComputerCase',
            'Motherboard',
            'Processor',
            'VideoCard',
            'CpuCooler',
            'Printer',
            'Ram',
            'Monitor',
            'MemoryCard',
            'Mouse',
            'Cell',
            'UsbFlashDrive',
            'Television',
            'Camera',
            'Projector',
            'AllInOne',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'VideoGameConsole',
            'Ups',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)

        category_paths = [
            ['351', ['ExternalStorageDrive'],
             'Home > Almacenamiento > Disco Duro Externo', 1],
            ['348', ['ExternalStorageDrive'],
             'Home > Almacenamiento > Almacenamiento en Red', 1],
            ['352', ['StorageDrive'],
             'Home > Almacenamiento > Disco Duro Interno', 1],
            ['350', ['SolidStateDrive'],
             'Home > Almacenamiento > Unidad Estado Solido SSD', 1],
            ['475', ['Tablet'],
             'Home > Apple > IPad', 1],
            ['369', ['Tablet'],
             'Home > Tablets y Accesorios > Tablets', 1],
            ['365', ['Notebook'],
             'Home > Computadores y Notebooks > '
             'Notebook Corporativo y Comercial', 1],
            ['474', ['Notebook'],
             'Home > Apple > Mac', 1],
            ['556', ['Notebook'],
             'Home > Computadores y Notebooks > Notebook Gamer', 1],
            ['344', ['StereoSystem'],
             'Home > Accesorios > Parlantes', 1],
            # ['360', ['StereoSystem'],
            #  'Home > Audio y Video > Equipos de Música', 1],
            # ['362', 'StereoSystem'],    # Home Theater
            # ['512', 'StereoSystem'],    # 512
            # ['359', 'OpticalDiskPlayer'],
            ['376', ['PowerSupply'],
             'Home > Componentes para PC > Fuentes de Poder', 1],
            ['375', ['ComputerCase'],
             'Home > Componentes para PC > Gabinetes', 1],
            ['377', ['Motherboard'],
             'Home > Componentes para PC > Placas Madres', 1],
            ['378', ['Processor'],
             'Home > Componentes para PC > Procesadores', 1],
            ['379', ['VideoCard'],
             'Home > Componentes para PC > Tarjetas de Video', 1],
            ['484', ['CpuCooler'],
             'Home > Componentes para PC > Refrigeración y Ventiladores', 1],
            ['396', ['Printer'],
             'Home > Impresoras y Escáneres > Impresora a Tinta', 1],
            ['398', ['Printer'],
             'Home > Impresoras y Escáneres > Multifuncional', 1],
            ['394', ['Printer'],
             'Home > Impresoras y Escáneres > Impresora Láser', 1],
            ['409', ['Ram'],
             'Home > Memorias > Memoria RAM PC', 1],
            ['410', ['Ram'],
             'Home > Memorias > Memoria RAM Notebook', 1],
            ['415', ['Monitor'],
             'Home > Monitores y Proyectores > Monitor', 1],
            ['411', ['MemoryCard'],
             'Home > Memorias > Memoria Flash', 1],
            ['341', ['Mouse'],
             'Home > Accesorios > Mouse', 1],
            ['459', ['Cell'],
             'Home > Celulares y Accesorios > Teléfonos Móviles', 1],
            ['412', ['UsbFlashDrive'],
             'Home > Memorias > Pendrive', 1],
            ['417', ['Television'],
             'Home > Monitores y Proyectores > Televisor', 1],
            ['387', ['Camera'],
             'Home > Imagen Digital > Cámaras Digitales', 1],
            ['416', ['Projector'],
             'Home > Monitores y Proyectores > Proyectores', 1],
            ['370', ['AllInOne'],
             'Home > Computadores y Notebooks > All In One', 1],
            ['342', ['Keyboard'],
             'Home > Accesorios > Teclados', 1],
            ['339', ['KeyboardMouseCombo'],
             'Home > Accesorios > Kit Teclados Mouse', 1],
            ['337', ['Headphones'],
             'Home > Accesorios > Audífonos', 1],
            ['357', ['VideoGameConsole'],
             'Home > Audio y Video > Consolas', 1],
            ['463', ['Ups'],
             'Home > UPS y protección de poder > UPS y respaldo de energía',
             1],
        ]

        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            p = 1
            current_position = 1

            local_product_urls = []

            while True:
                if p >= 80:
                    raise Exception('Page overflow for: {}'.format(
                        category_id))

                url = 'https://www.spdigital.cl/categories/view/{}/page:' \
                      '{}?o=withstock'.format(category_id, p)

                response = cls._retrieve_page(session, url)
                soup = BeautifulSoup(response.text, 'html5lib')

                product_containers = soup.findAll('div', 'product-item-mosaic')

                if not product_containers:
                    if p == 1:
                        raise Exception('Empty category: {}'.format(
                            category_id))
                    else:
                        break

                done = False

                for container in product_containers:
                    product_url = 'https://www.spdigital.cl' + \
                           container.find('a')['href']
                    if product_url in local_product_urls:
                        done = True
                        break

                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': current_position
                    })

                    local_product_urls.append(product_url)
                    current_position += 1

                if done:
                    break
                p += 1

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = cls._retrieve_page(session, url)
        soup = BeautifulSoup(response.text, 'html.parser')

        part_number = soup.find('span', {'id': '_sku'})

        if not part_number:
            return []

        if soup.find('span', 'product-view-price-a-pedido'):
            return []

        part_number = part_number.text.strip()

        name = soup.find('h1').text.strip()
        sku = [x for x in url.split('/') if x][-1]

        if soup.find('a', 'stock-amount-cero') or \
                not soup.find('div', 'product-view-stock'):
            stock = 0
        else:
            stock_text = soup.find('div', 'product-view-stock').find(
                'span').text

            if 'preventa' in stock_text.lower():
                stock = -1
            else:
                stock_overflow, stock_value = re.match(r'(.*?)(\d+) UNIDADES',
                                                       stock_text).groups()

                if stock_overflow:
                    stock = -1
                else:
                    stock = int(stock_value)

        containers = soup.findAll('span', 'product-view-cash-price-value')

        offer_price = Decimal(remove_words(containers[0].text))
        normal_price = Decimal(remove_words(containers[1].text))

        if normal_price < offer_price:
            offer_price = normal_price

        tabs = [
            soup.find('div', 'product-description-tab'),
            soup.find('div', {'data-tab': 'specifications'})
        ]

        description = ''

        for tab in tabs:
            if not tab:
                continue
            description += html_to_markdown(
                str(tab), 'https://www.spdigital.cl') + '\n\n'

        picture_containers = soup.findAll('a', {'rel': 'lightbox'})

        picture_urls = []
        for container in picture_containers:
            picture_url = container.find('img')['src'].replace(' ', '%20')
            if 'http' not in picture_url:
                picture_url = 'https://www.spdigital.cl' + picture_url
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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

    @classmethod
    def _retrieve_page(cls, session, url, retries=5):
        print(url)
        try:
            return session.get(url, timeout=90)
        except Exception:
            if retries:
                return cls._retrieve_page(session, url, retries-1)
            else:
                raise
