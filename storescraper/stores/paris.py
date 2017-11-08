import json
import random
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Paris(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'HomeTheater',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Projector',
            'VideoGameConsole',
            'Monitor',
            'AllInOne',
            'AirConditioner',
            'WaterHeater',
            'SolidStateDrive',
            'SpaceHeater',
            'Smartwatch',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['51206207', 'Notebook'],
            ['51325099', 'Notebook'],
            ['51445598', 'Notebook'],
            ['51436669', 'Television'],
            ['51206208', 'Tablet'],
            ['51206164', 'Refrigerator'],
            ['51206220', 'Printer'],  # Multifuncionales
            ['51206221', 'Printer'],  # Laser
            ['51206182', 'Oven'],
            ['51206183', 'Oven'],
            ['51206185', 'VacuumCleaner'],
            ['51206169', 'WashingMachine'],
            ['51206171', 'WashingMachine'],
            ['51206170', 'WashingMachine'],
            ['51296122', 'Cell'],
            ['51206214', 'Cell'],
            ['51206145', 'Camera'],
            ['51206144', 'Camera'],
            ['51568122', 'StereoSystem'],   # Microcomponente
            ['51568123', 'StereoSystem'],   # Minicomponente
            # ['51437112', 'OpticalDiskPlayer'],
            ['51568103', 'HomeTheater'],  # Home theater
            ['51206225', 'ExternalStorageDrive'],
            ['51206226', 'UsbFlashDrive'],
            ['51225099', 'MemoryCard'],
            ['51206217', 'Projector'],
            ['51206137', 'VideoGameConsole'],
            ['51334105', 'AllInOne'],
            ['51219599', 'AirConditioner'],
            ['51281600', 'WaterHeater'],
            ['51206179', 'SpaceHeater'],
            ['51378608', 'Smartwatch'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for path, local_category in category_paths:
            if category != local_category:
                continue

            random_component = random.randint(1, 1000)

            category_url = 'https://www.paris.cl/webapp/wcs/stores/servlet/' \
                           'AjaxCatalogSearchResultView?sType=SimpleSearch&' \
                           'pageSize=1000&storeId=10801&categoryId={}&' \
                           'rnd={}'.format(path, random_component)
            print(category_url)
            soup = BeautifulSoup(session.get(
                category_url, timeout=30).text, 'html.parser')

            product_containers = soup.findAll('td', 'item')

            if not product_containers:
                raise Exception('Empty category: {} - {}'.format(
                    category, path))

            for cell in product_containers:
                product_link = cell.find('div', 'tertiary_button').find('a')

                product_js = product_link['onclick']
                # print(product_js)
                product_id = re.search(
                    r"showPopup\('(\d+)'", product_js)
                if not product_id:
                    # "Producto con precio pendiente"
                    continue
                product_id = product_id.groups()[0]
                product_url = 'https://www.paris.cl/tienda/ProductDisplay?' \
                              'storeId=10801&productId=' + product_id
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        return cls._products_for_url(url, category=category,
                                     extra_args=extra_args, retries=5)

    @classmethod
    def _products_for_url(cls, url, category, extra_args, retries):
        session = session_with_proxy(extra_args)

        random_component = random.randint(1, 1000)
        url_for_request = '{}&rnd={}'.format(url, random_component)

        page_source = session.get(url_for_request, timeout=30).text
        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('h1', {'role': 'main'}):
            return []

        name = soup.find('h1', {'id': 'catalog_link'})

        if not name:
            return []

        name = name.text.strip()

        sku = soup.find('div', {'id': 'detalles-sku'}).text.replace(
            'SKU: ', '').strip()
        normal_price = re.search(
            r"var offerPrice_DL = '(\d*)'", page_source).groups()[0]
        if not normal_price:
            return []

        normal_price = Decimal(normal_price)

        offer_price = re.search(
            r"var tcPrice_DL = '(\d*)'", page_source).groups()[0]
        if offer_price:
            offer_price = Decimal(offer_price)
        else:
            offer_price = normal_price

        stock = re.search(
            r"var itemQuantity_DL = '(.+)'",
            page_source)
        if stock:
            stock = int(stock.groups()[0].replace('.', ''))
        else:
            stock = 0

        if stock == 0:
            if retries:
                return cls._products_for_url(
                    url, category=category, extra_args=extra_args,
                    retries=retries-1)
            else:
                pass

        description = html_to_markdown(str(soup.find('div', 'description')))

        image_id = re.search(
            r"var productImagePartNumber = '(.+)';", page_source).groups()[0]

        pictures_resource_url = 'https://imagenes.paris.cl/is/image/' \
                                'Cencosud/{}?req=set,json'.format(image_id)
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      session.get(pictures_resource_url).text).groups()[0])
        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https://imagenes.paris.cl/is/image/{}?scl=1.0' \
                          ''.format(picture_entry['i']['n'])
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
