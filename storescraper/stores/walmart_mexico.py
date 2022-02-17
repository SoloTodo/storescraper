import json

import re

from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class WalmartMexico(Store):
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
            'KeyboardMouseCombo',
            'Monitor',
            'Tablet',
            'Notebook',
            'Printer',
            'Cell',
            'Television',
            'AllInOne',
            'VideoGameConsole'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        api_url = 'https://www.walmart.com.mx/api/page/browse/'
        base_url = 'https://www.walmart.com.mx'

        category_paths = [
            ['computadoras/accesorios-para-computadoras/discos-duros/'
             '_/N-1dowb3hZ1kv2jt7?Nval=%2F_%2FN-1dowb3hZ1kv2jt7',
             'StorageDrive'],
            ['computadoras/accesorios-para-computadoras/discos-duros/'
             '_/N-1dowb3hZkzndmn?Nval=%2F_%2FN-1dowb3hZkzndmn',
             'SolidStateDrive'],
            ['computadoras/componentes-de-computadoras/tarjetas-madre?',
             'Motherboard'],
            ['computadoras/componentes-de-computadoras/procesadores?',
             'Processor'],
            ['computadoras/componentes-de-computadoras/'
             'enfriadores-y-ventiladores?', CPU_COOLER],
            ['computadoras/componentes-de-computadoras/memoria-ram?', 'Ram'],
            ['computadoras/componentes-de-computadoras/tarjetas-de-video?',
             'VideoCard'],
            ['computadoras/componentes-de-computadoras/fuentes-de-poder?',
             'PowerSupply'],
            ['computadoras/componentes-de-computadoras/'
             'torres-y-gabinetes-de-pc?', 'ComputerCase'],
            ['computadoras/accesorios-para-computadoras/'
             'mouse-teclados-y-webcams?', 'Mouse'],
            ['computadoras/proyectores/monitores?', 'Monitor'],
            ['computadoras/tablets/todas-las-tablets?', 'Tablet'],
            ['computadoras/tablets/ipad?', 'Tablet'],
            ['computadoras/tablets/tablets-android?', 'Tablet'],
            ['computadoras/laptops/todas-las-laptops?', 'Notebook'],
            ['computadoras/laptops/macbooks?', 'Notebook'],
            ['computadoras/laptops/chromebooks?', 'Notebook'],
            ['computadoras/laptops/notebooks?', 'Notebook'],
            ['computadoras/laptops/ultrabooks?', 'Notebook'],
            ['computadoras/laptops/2-en-1-y-touchscreen?', 'Notebook'],
            ['computadoras/impresoras-y-scanners/multifuncionales?',
             'Printer'],
            ['computadoras/impresoras-y-scanners/impresoras?', 'Printer'],
            ['celulares/smartphones/celulares-desbloqueados?', 'Cell'],
            ['celulares/smartphones/at-t?', 'Cell'],
            ['celulares/smartphones/movistar?', 'Cell'],
            ['celulares/smartphones/telcel?', 'Cell'],
            ['tv-y-video/pantallas/65-o-mas-pulgadas?', 'Television'],
            ['tv-y-video/pantallas/55-a-64-pulgadas?', 'Television'],
            ['tv-y-video/pantallas/47-a-54-pulgadas?', 'Television'],
            ['tv-y-video/pantallas/37-a-46-pulgadas?', 'Television'],
            ['tv-y-video/pantallas/28-a-36-pulgadas?', 'Television'],
            ['tv-y-video/pantallas/27-pulgadas-o-menos?', 'Television'],
            ['tv-y-video/pantallas/4k-ultra-hd?', 'Television'],
            ['tv-y-video/pantallas/smart-tv?', 'Television'],
            ['tv-y-video/pantallas/todas?', 'Television'],
            ['computadoras/computadoras-de-escritorio/all-in-one?',
             'AllInOne'],
            ['videojuegos/xbox-one/consolas?', 'VideoGameConsole'],
            ['videojuegos/nintendo/consolas?', 'VideoGameConsole'],
            ['videojuegos/playstation-4/consolas-consola-ps4?',
             'VideoGameConsole'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            current_index = 0
            page_size = 24

            while True:
                category_url = '{}{}&Nrpp=24&No={}'.format(
                    api_url, category_path, current_index)
                print(category_url)
                page_data = json.loads(session.get(category_url).text)
                products_data = page_data[
                    'contents'][0]['mainArea'][-1]['records']

                if not products_data:
                    break

                for product in products_data:
                    product_url = product['attributes']['productSeoUrl'][0]
                    product_url = "{}{}".format(base_url, product_url)

                    product_urls.append(product_url)

                current_index += page_size

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        product_id = url.split('_')[-1]
        api_url = 'https://www.walmart.com.mx/api/rest/model/atg/commerce/' \
                  'catalog/ProductCatalogActor/getProduct?id={}'\
            .format(product_id)

        product_data = json.loads(session.get(api_url).text)['product']

        name = product_data['displayName']
        sku = product_data['childSKUs'][0]['id']
        stock = -1

        price = Decimal(
            product_data['childSKUs'][0][
                'offerList'][0]['priceInfo']['specialPrice'])

        image_url_base = 'https://res.cloudinary.com/walmart-labs/image/'\
                         'upload/w_960,dpr_auto,f_auto,q_auto:best/mg{}'

        primary_image = product_data['childSKUs'][0]['images']['large']
        picture_urls = [image_url_base.format(primary_image)]

        if 'secondaryImages' in product_data['childSKUs'][0]:
            secondary_images = product_data['childSKUs'][0]['secondaryImages']
            for image in secondary_images:
                picture_urls.append(image_url_base.format(image['large']))

        if 'longDescription' in product_data:
            description = product_data['longDescription']
        else:
            description = product_data['description']

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
