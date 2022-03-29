import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, VIDEO_GAME_CONSOLE, \
    GAMING_DESK, MICROPHONE, CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class PcNitro(Store):
    @classmethod
    def categories(cls):
        return [
            'AllInOne',
            'Notebook',
            'Tablet',
            'ComputerCase',
            CPU_COOLER,
            'Motherboard',
            'PowerSupply',
            'Processor',
            'VideoCard',
            'Ups',
            'MemoryCard',
            'Ram',
            'UsbFlashDrive',
            'Headphones',
            'Keyboard',
            'KeyboardMouseCombo',
            'Mouse',
            'StereoSystem',
            'Monitor',
            'Television',
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Cell',
            'Printer',
            GAMING_CHAIR,
            VIDEO_GAME_CONSOLE,
            GAMING_DESK,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['27-todo-en-uno', 'AllInOne'],
            ['29-portátiles', 'Notebook'],
            ['216-notebook-gaming', 'Notebook'],
            ['31-tablet', 'Tablet'],
            ['40-cajas-gabinetes', 'ComputerCase'],
            ['41-ventiladores-y-sist-de-enfriamiento', CPU_COOLER],
            ['42-tarjeta-madre-placa-madre', 'Motherboard'],
            ['43-fuentes-de-poder', 'PowerSupply'],
            ['44-procesadores', 'Processor'],
            ['45-tarjetas-gráficas-vídeo', 'VideoCard'],
            ['36-ups-respaldo-energía', 'Ups'],
            ['46-tarjetas-de-memoria-flash', 'MemoryCard'],
            ['48-memorias-ram', 'Ram'],
            ['49-unidades-flash-usb', 'UsbFlashDrive'],
            ['60-auriculares-y-manos-libres', 'Headphones'],
            ['120-auriculares', 'Headphones'],
            ['61-teclados-teclado-numéricos', 'Keyboard'],
            ['62-combo-teclado-mouse', 'KeyboardMouseCombo'],
            ['63-mouse', 'Mouse'],
            ['64-parlantes-bocinas-cornetas', 'StereoSystem'],
            ['123-parlantes-bocinas-cornetas', 'StereoSystem'],
            ['67-monitores', 'Monitor'],
            ['70-televisores', 'Television'],
            ['52-disco-duros-externos', 'ExternalStorageDrive'],
            ['54-disco-duros-internos', 'StorageDrive'],
            ['57-discos-de-estado-solido', 'SolidStateDrive'],
            ['138-celulares', 'Cell'],
            ['156-impresoras-ink-jet', 'Printer'],
            ['158-impresoras-laser', 'Printer'],
            ['159-impresoras-multifunción', 'Printer'],
            ['160-impresoras-fotográficas', 'Printer'],
            ['174-sillas-gaming', GAMING_CHAIR],
            ['315-consolas-de-juegos', VIDEO_GAME_CONSOLE],
            ['175-escritorio', GAMING_DESK],
            ['121-microfonos', MICROPHONE]

        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_id, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 40:
                    raise Exception('Page overflow')

                url = 'https://pcnitro.cl/{}?page={}'\
                    .format(category_id, page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                products = soup.findAll('div', 'product-description')

                if not products:
                    if page == 1:
                        logging.warning('Empty path ' + url)
                    break

                for product in products:
                    product_url = product.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text

        model_container = soup.find('strong', text='MODELO:\xa0')
        if model_container:
            model = model_container.parent.parent.findAll('strong')
            if len(model) > 1:
                name = '{} ({})'.format(name, model[1].text.strip())

        sku = soup.find('input', {'name': 'id_product'})['value']
        stock = 0
        stock_container = soup.find('div', 'product-quantities')

        if stock_container:
            stock = int(soup.find('div', 'product-quantities').find(
                'span')['data-stock'])

        price = Decimal(soup.find('span', {'itemprop': 'price'})['content'])

        pictures = soup.find('ul', 'product-images').findAll('li')
        picture_urls = [p.find('img')['data-image-large-src']
                        for p in pictures]

        description = html_to_markdown(str(soup.find(
            'div', 'product-description')))

        pn_container = soup.find('span', {'itemprop': 'sku'})
        if pn_container:
            part_number = pn_container.text.strip()[:50]
        else:
            part_number = None

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
            picture_urls=picture_urls,
            part_number=part_number
        )

        return [p]
