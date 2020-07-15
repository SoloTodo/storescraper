import html
import json
import demjson
import re
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown


class MercadolibreChile(Store):
    @classmethod
    def categories(cls):
        categories = set()
        stores_paths = cls._category_paths().values()
        for store_paths in stores_paths:
            for store_path in store_paths:
                categories.add(store_path[1])
        return list(categories)

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = requests.Session()
        product_urls = []

        for store_extension, store_paths in cls._category_paths().items():
            for category_path, local_category in store_paths:
                if local_category != category:
                    continue

                category_url = 'https://listado.mercadolibre.cl/{}/' \
                               '{}'.format(category_path, store_extension)
                print(category_url)
                response = session.get(category_url)
                soup = BeautifulSoup(response.text,
                                     'html.parser')

                if soup.find('div', 'zrp-offical-message'):
                    raise Exception('Invalid category: ' + category_url)

                containers = soup.findAll('li', 'results-item')

                if not containers:
                    containers = soup.findAll('li', 'ui-search-layout__item')

                if not containers:
                    raise Exception('Empty category: ' + category_url)

                for container in containers:
                    product_url = container.find('a')['href'].split(
                        '?')[0].split('#')[0]
                    product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = requests.Session()
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        products = []

        name = soup.find('meta', {'name': 'twitter:title'})['content'].strip()
        description = html_to_markdown(
            str(soup.find('section', 'item-description')))

        variations = re.search(r'meli.Variations\(\{([\S\s]+?)}\);',
                               page_source)

        if not variations:
            pictures_data = json.loads(html.unescape(
                soup.find('div', 'gallery-content')['data-full-images']))
            picture_urls = [e['src'] for e in pictures_data]
            pricing_str = re.search(
                r'dataLayer = ([\S\s]+?);', page_source).groups()[0]
            pricing_data = json.loads(pricing_str)[0]
            sku = pricing_data['itemId']
            price = Decimal(pricing_data['localItemPrice'])
            stock = pricing_data['availableStock']

            products.append(Product(
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
            ))

        else:
            variations_str = variations.groups()[0]
            variations_data = demjson.decode("{"+variations_str+"}")['model']

            for variation in variations_data:
                key = str(variation['id'])
                sku = soup.find('input', {'name': 'itemId'})['value']
                v_suffix = variation[
                    'attribute_combinations'][0]['value_name']
                v_name = name + "({})".format(v_suffix)
                v_url = url.split('?')[0] + "?variation={}".format(key)
                price = Decimal(variation['price'])
                stock = variation['available_quantity']
                picture_url_base = 'https://mlc-s2-p.mlstatic.com/{}-F.jpg'
                picture_urls = [picture_url_base.format(p_id)
                                for p_id in variation['picture_ids']]

                products.append(Product(
                    v_name,
                    cls.__name__,
                    category,
                    v_url,
                    url,
                    key,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    description=description,
                    picture_urls=picture_urls
                ))

        return products

    @classmethod
    def _category_paths(cls):
        return {
            '_Tienda_acer': [
                # ('computacion/notebooks', 'Notebook'),
                # ('almacenamiento', 'ExternalStorageDrive'),
                ('tablets-accesorios', 'Tablet'),
                # ('monitores-accesorios', 'Monitor'),
            ],
            '_Tienda_cintegral': [
                ('notebooks-accesorios', 'Notebook'),
                ('pc-escritorio', 'AllInOne'),
                ('almacenamiento', 'SolidStateDrive'),
            ],
            '_Tienda_corsair': [
                # ('notebooks-accesorios', 'CpuCooler'),
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                # ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                # ('componentes-pc', 'PowerSupply'),
            ],
            '_Tienda_cougar': [
                # ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                # ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                # ('webcams-audio-pc', 'Headphones'),
                # ('electronica', 'Headphones'),
            ],
            '_Tienda_hp': [
                ('computacion/notebooks', 'Notebook'),
                ('pc-escritorio', 'AllInOne'),
                ('computacion/impresoras/impresoras', 'Printer'),
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                # ('almacenamiento', 'AllInOne'),
                ('monitores-accesorios', 'Monitor'),
            ],
            '_Tienda_huawei': [
                ('celulares-telefonia/celulares', 'Cell'),
                ('smartwatches-accesorios', 'Wearable'),
                ('notebooks-accesorios', 'Notebook'),
                ('tablets-accesorios', 'Tablet'),
                ('audio-audifonos', 'Headphones'),
                # ('electronica/audio-hogar/parlantes-subwoofers',
                # 'Headphones'),
            ],
            '_Tienda_hyperx': [
                # ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                # ('webcams-audio-pc', 'Headphones'),
            ],
            '_Tienda_lenovo': [
                # ('pc-escritorio-all-in-one', 'AllInOne'),
            ],
            '_Tienda_logitech': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('mouses-teclados-controles-kits-mouse-teclado',
                 'KeyboardMouseCombo'),
                ('webcams-audio-pc', 'StereoSystem'),
            ],
            '_Tienda_logitech-g': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                # ('webcams-audio-pc-audifonos', 'Headphones'),
                # ('electronica', 'Headphones'),
                # ('webcams-audio-pc-parlantes', 'StereoSystem'),
            ],
            '_Tienda_marvo': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc-audifonos', 'Headphones'),
                # ('webcams-audio-pc-parlantes', 'StereoSystem'),
            ],
            '_Tienda_ozone': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc', 'Headphones'),
                ('videojuegos', 'Headphones'),
            ],
            '_Tienda_pc-factory_OfficialStoreId_810': [
                ('celulares-telefonia', 'Cell'),
                ('computacion', 'Notebook'),
            ],
            '_Tienda_primus': [
                # ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
            ],
            '_Tienda_razer': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc', 'Headphones'),
            ],
            '_Tienda_redragon': [
                # ('mouses-teclados-controles', 'Keyboard'),
            ],
            '_Tienda_seagate': [
                ('almacenamiento-discos-accesorios-duros-ssds/externo',
                 'ExternalStorageDrive'),
                ('almacenamiento-discos-accesorios-duros-ssds/interno',
                 'StorageDrive'),
            ],
            '_Tienda_trust': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
            ],
            '_Tienda_western-digital': [
                ('almacenamiento-discos-duros-removibles-accesorios',
                 'SolidStateDrive'),
                ('almacenamiento-discos-accesorios-duros-ssds/externo',
                 'ExternalStorageDrive'),
                ('almacenamiento-discos-accesorios-duros-ssds/interno',
                 'StorageDrive'),
            ],
            '_Tienda_xpg': [
                ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                ('webcams-audio-pc', 'Headphones'),
            ],
            '_Tienda_xtech': [
                # ('computacion/perifericos-accesorios/teclados', 'Keyboard'),
                ('computacion/perifericos-accesorios/mouses', 'Mouse'),
                # ('componentes-pc', 'PowerSupply'),
                # ('audio-audifonos', 'Headphones'),
            ],
            '_Tienda_blu': [
                ('celulares-telefonia/celulares', 'Cell'),
            ],
            '_Tienda_kingston': [
                ('celulares-telefonia', 'MemoryCard'),
                ('almacenamiento-discos-accesorios', 'SolidStateDrive'),
                ('almacenamiento-pen-drives', 'UsbFlashDrive'),
            ],
            '_Tienda_motorola': [
                ('audio', 'Headphones'),
                ('celulares-telefonia/celulares', 'Cell'),
                ('celulares-telefonia/accesorios-celulares', 'StereoSystem'),
            ],
            '_Tienda_nokia': [
                ('celulares-telefonia/celulares', 'Cell'),
            ],
            '_Tienda_daewoo': [
                ('refrigeracion', 'Refrigerator'),
                ('lavado-y-secado-de-ropa', 'WashingMachine'),
            ],
            '_Tienda_xiaomi': [
                ('celulares-telefonia/celulares', 'Cell'),
                ('smartwatches-accesorios-smartwatch', 'Wearable'),
                ('audio', 'Headphones'),
            ]
        }
