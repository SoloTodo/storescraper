import json

from bs4 import BeautifulSoup
from decimal import Decimal

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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):

        category_urls = [
            ['tecnologia/partes-y-piezas/almacenamiento/discos-duros/'
             'discos-externos', 'ExternalStorageDrive'],
            ['tecnologia/partes-y-piezas/almacenamiento/discos-duros/'
             'discos-internos', 'StorageDrive'],
            ['tecnologia/partes-y-piezas/almacenamiento/discos-duros/'
             'ssd', 'SolidStateDrive'],
            ['tecnologia/equipos/notebooks', 'Notebook'],
            ['audio-y-video/parlantes', 'StereoSystem'],
            # ['tecnologia/componentes-pc/fuente-de-poder', 'PowerSupply'],
            ['tecnologia/componentes-pc/gabinetes', 'ComputerCase'],
            ['tecnologia/componentes-pc/placas-madres', 'Motherboard'],
            ['tecnologia/componentes-pc/procesadores', 'Processor'],
            ['tecnologia/componentes-pc/tarjetas-de-video', 'VideoCard'],
            ['tecnologia/partes-y-piezas/impresoras', 'Printer'],
            ['tecnologia/partes-y-piezas/memorias-ram', 'Ram'],
            ['tecnologia/partes-y-piezas/monitores', 'Monitor'],
            ['tecnologia/accesorios/mouse', 'Mouse'],
            ['movil/celulares', 'Cell'],
            ['tecnologia/partes-y-piezas/proyectores', 'Projector'],
            ['tecnologia/equipos/all-in-one', 'AllInOne'],
            ['tecnologia/accesorios/teclados', 'Keyboard'],
            ['audio-y-video/audifonos', 'Headphones']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 15:
                    raise Exception('Page overflow')

                page_url = 'https://www.mercadotech.cl/t/{}?page={}'\
                    .format(category_path, page)

                print(page_url)

                soup = BeautifulSoup(session.get(page_url).text, 'html.parser')

                product_content = soup.find(
                    'div', {'data-hook': 'homepage_products'})

                if page == 1 and not product_content:
                    raise Exception('No products for url {}'.format(page_url))

                if not product_content:
                    break

                product_containers = product_content.find('div', 'row')\
                    .findAll('div', 'col-sm-4')

                for product_container in product_containers:
                    product_url = 'https://www.mercadotech.cl{}'.format(
                        product_container.find('a')['href'])
                    product_urls.append(product_url)

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

        name = json_data['name']
        sku = json_data['sku']

        potential_pns = soup.findAll('li', 'extended d-none')
        part_number = None
        for ppn in potential_pns:
            contents = [a for a in ppn.contents if a not in ['\n']]
            if contents[0].text == 'part_number:':
                part_number = contents[1].text

        stock = 0

        if 'bad box' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        if json_data['offers']['availability'] == 'InStock':
            stock = -1

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
