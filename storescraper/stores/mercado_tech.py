import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR, USB_FLASH_DRIVE, \
    MEMORY_CARD, TELEVISION, CPU_COOLER, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, \
    session_with_proxy


class MercadoTech(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Notebook',
            'StereoSystem',
            'PowerSupply',
            'ComputerCase',
            'Motherboard',
            'Processor',
            'VideoCard',
            'Printer',
            'Ram',
            'Monitor',
            'Mouse',
            'Cell',
            # 'Projector',
            'AllInOne',
            'Keyboard',
            'Headphones',
            GAMING_CHAIR,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            TELEVISION,
            CPU_COOLER,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):

        category_urls = [
            ['tecnologia/partes-y-piezas/almacenamiento/discos-duros/'
             'discos-externos', 'ExternalStorageDrive'],
            ['tecnologia/partes-y-piezas/almacenamiento/discos-duros/'
             'discos-internos/mecanicos', 'StorageDrive'],
            ['tecnologia/partes-y-piezas/almacenamiento/discos-duros/'
             'ssd', 'SolidStateDrive'],
            ['tecnologia/equipos/notebooks', 'Notebook'],
            ['audio-y-video/parlantes', 'StereoSystem'],
            ['tecnologia/componentes-pc/fuente-de-poder', 'PowerSupply'],
            ['tecnologia/componentes-pc/gabinetes/gabinetes', 'ComputerCase'],
            ['tecnologia/componentes-pc/placas-madres', 'Motherboard'],
            ['tecnologia/componentes-pc/procesadores/amd', 'Processor'],
            ['tecnologia/componentes-pc/procesadores/intel', 'Processor'],
            ['tecnologia/componentes-pc/procesadores/accesorios-cpu',
             CPU_COOLER],
            ['tecnologia/componentes-pc/gabinetes/accesorios', CPU_COOLER],
            ['tecnologia/componentes-pc/tarjetas-de-video', 'VideoCard'],
            ['tecnologia/partes-y-piezas/impresoras', 'Printer'],
            ['tecnologia/partes-y-piezas/memorias-ram', 'Ram'],
            ['tecnologia/partes-y-piezas/monitores/monitores', 'Monitor'],
            ['tecnologia/partes-y-piezas/monitores/televisores', TELEVISION],
            ['tecnologia/accesorios/mouse', 'Mouse'],
            ['movil/celulares', 'Cell'],
            ['tecnologia/partes-y-piezas/proyectores', 'Projector'],
            ['tecnologia/equipos/all-in-one', 'AllInOne'],
            ['tecnologia/accesorios/teclados', 'Keyboard'],
            ['audio-y-video/audifonos', 'Headphones'],
            ['tecnologia/accesorios/ergonomia/sillas', GAMING_CHAIR],
            ['tecnologia/partes-y-piezas/almacenamiento/pendrives',
             USB_FLASH_DRIVE],
            ['tecnologia/partes-y-piezas/almacenamiento/memorias-sd',
             MEMORY_CARD],
            ['tecnologia/accesorios/accesorios/microfonos', MICROPHONE]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 20:
                    raise Exception('Page overflow')

                page_url = 'https://www.mercadotech.cl/t/{}?page={}'\
                    .format(category_path, page)

                print(page_url)

                soup = BeautifulSoup(session.get(page_url).text, 'html.parser')

                product_content = soup.find(
                    'div', {'data-hook': 'homepage_products'})

                if not product_content:
                    if page == 1:
                        logging.warning(
                            'No products for url {}'.format(page_url))
                    break

                product_containers = product_content.find('div', 'row')\
                    .findAll('div', 'col-sm-4')

                for product_container in product_containers:
                    product_url = 'https://www.mercadotech.cl{}'.format(
                        product_container.find('a')['href'])
                    product_urls.append(product_url.split('?')[0])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        data = soup.find('script', {'type': 'application/ld+json'}).text
        json_data = json.loads(data)[0]

        name = json_data['name'][:250]
        sku = json_data['sku']

        potential_pns = soup.findAll(
            'div', 'add-to-cart-form-general-availability')
        part_number = None
        for ppn in potential_pns:
            if 'PN: ' in ppn.text:
                part_number = ppn.text.split('PN: ')[1].strip()

        if 'bad box' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        if json_data['offers']['availability'] == 'https://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        price = Decimal(json_data['offers']['price'])
        picture_containers = soup.findAll('div', 'carousel-inner')
        picture_urls = []
        if picture_containers:
            picture_containers = [
                c.find('img') for c in picture_containers[-1].findAll(
                    'div', 'product-carousel-item-squared')]

            for picture_container in picture_containers:
                try:
                    picture_url = picture_container['data-src']
                except KeyError:
                    picture_url = picture_container['src']

                picture_urls.append(picture_url)

        description = html_to_markdown(json_data['description'] or '')

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
            part_number=part_number,
            picture_urls=picture_urls,
            description=description,
            condition=condition
        )

        return [p]
