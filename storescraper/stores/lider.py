import json
import urllib
import xml.etree.ElementTree as ET

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Lider(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
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
            'VideoGameConsole',
            'AllInOne',
            'Projector',
            'SpaceHeater',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['Tecnología/Tv-y-Video/Televisores/_/N-j78dbl', 'Television'],
            ['Tecnología/Tv-y-Video/DVDs-y-Blu-Ray-/_/N-1q0ac99',
             'OpticalDiskPlayer'],
            ['Computación/Computación/Notebooks/_/N-8ca5vv', 'Notebook'],
            ['Computación/Computación/Convertibles/_/N-164r8qj', 'Notebook'],
            ['Computación/Computación/Gamers/_/N-y276sd', 'Notebook'],
            ['Computación/Computadores/Tablets/_/N-1yeeydi', 'Tablet'],
            ['Electrohogar/Refrigeración/Freezers/_/N-1rld1f3',
             'Refrigerator'],
            ['Electrohogar/Refrigeración/Frigobar/_/N-1ulwq6c',
             'Refrigerator'],
            ['Electrohogar/Refrigeración/No-Frost/_/N-7wqjz8',
             'Refrigerator'],
            ['Electrohogar/Refrigeración/Side-By-Side/_/N-ihia7d',
             'Refrigerator'],
            ['Electrohogar/Refrigeración/Frio-Directo/_/N-1vjdiki',
             'Refrigerator'],
            # ['Electrohogar/Refrigeración/Frio-Combinado/_/N-1p622ha',
            #  'Refrigerator'],
            ['Impresoras/Impresoras-y-Scanner/_/N-wpy7wh', 'Printer'],
            ['Electrohogar/Electrodomésticos/Hornos-Eléctricos/_/N-wzp80k',
             'Oven'],
            ['Electrohogar/Electrodomésticos/Microondas/_/N-1v8tank', 'Oven'],
            ['Electrohogar/Electrodomésticos/Aspirado-y-Limpieza/_/N-dnvlsp',
             'VacuumCleaner'],
            ['Electrohogar/Lavado-y-Secado/Lavadoras-Superiores/_/N-g2rcn0',
             'WashingMachine'],
            ['Electrohogar/Lavado-y-Secado/Lavadoras-Frontales/_/N-l9pqcy',
             'WashingMachine'],
            ['Electrohogar/Lavado-y-Secado/Lavadoras-Secadoras/_/N-1xvutty',
             'WashingMachine'],
            ['Electrohogar/Lavado-y-Secado/Secadoras/_/N-3c1lrn',
             'WashingMachine'],
            ['Celulares-y-Fotografía/Celulares-y-Teléfonos/'
             'Equipos-Smartphone/_/N-1orftrb', 'Cell'],
            # ['Tecnología/Audio/Equipos-de-Música/_/N-ss8ejy',
            #  'StereoSystem'],
            ['Computación/Almacenamiento/Discos-Duros/_/N-1fztdr9',
             'ExternalStorageDrive'],
            ['Computación/Almacenamiento/Pendrives/_/N-fv774a',
             'UsbFlashDrive'],
            ['Computación/Almacenamiento/Tarjetas-de-Memoria/_/N-132igir',
             'MemoryCard'],
            ['Electrónica/Videojuegos/Consolas/_/N-nuwf4o',
             'VideoGameConsole'],
            ['Computación/Computadores/All-in-One-Desktops/_/N-7tgj44',
             'AllInOne'],
            ['Computación/Computadores/All-in-One-Desktops/_/N-7tgj44',
             'AllInOne'],
            ['Electrohogar/Calefacción/Estufas-Eléctricas/_/N-1o1r7ra',
             'SpaceHeater'],
            # ['Electrohogar/Calefacción/Estufas-a-Parafina/_/N-12llnaj',
            #  'SpaceHeater'],
            # ['Electrohogar/Calefacción/Estufas-a-Gas/_/N-a1fiac',
            #  'SpaceHeater'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            category_url = 'https://www.lider.cl/electrohogar/category/' \
                           '{}?Nrpp=1000'.format(urllib.parse.quote(
                               category_path))

            print(category_url)

            response = session.get(category_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            if '/product/' in response.url:
                product_id = response.url.split('/')[-1]
                product_urls.append('https://www.lider.cl/electrohogar/'
                                    'product/' + product_id)

            else:
                containers = soup.findAll('div', 'box-product')
                if not containers:
                    raise Exception('No products found for: {}'.format(
                        category_url))

                for container in containers:
                    product_path = container.findAll('a')[1]['href']
                    product_id = product_path.split('/')[-1]
                    product_url = 'https://www.lider.cl/electrohogar/' \
                                  'product/' + product_id

                    product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        pricing_data = soup.find('script', {'type': 'application/ld+json'})
        pricing_data = re.sub(r'/\*[\S\s]*\*/', '', pricing_data.text)

        pricing_json = json.loads(pricing_data)

        if 'brand' in pricing_json and 'name' in pricing_json:
            name = '{} {}'.format(pricing_json['brand'], pricing_json['name'])
        else:
            name = pricing_json['name']

        sku = pricing_json['sku']
        part_number = pricing_json.get('model')
        normal_price = Decimal(pricing_json['offers']['lowPrice'])
        offer_price = normal_price

        panels = [
            soup.find('div', {'id': 'longDescription'}),
            soup.find('div', {'id': 'specs'}),
        ]

        description = ''
        for panel in panels:
            if not panel:
                continue
            description += html_to_markdown(str(panel)) + '\n\n'

        # Availability

        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        request_body = 'productNumber={}&useImsStores=true&consolidate=true' \
                       ''.format(sku)
        avail_data = session.post(
            'https://www.lider.cl/electrohogar/includes/inventory/'
            'inventoryInformation.jsp', request_body).text
        avail_json = json.loads(avail_data)

        in_stock = int(avail_json['stockLevel'])

        if in_stock:
            stock = -1
        else:
            stock = 0

        # Pictures

        gallery_url = 'https://wlmstatic.lider.cl/contentassets/galleries/' \
                      '{}.xml'.format(sku)
        response = session.get(gallery_url)

        picture_urls = []
        if response.status_code == 200:
            root = ET.fromstring(response.text)

            for item in root.find('data').find('items').findall('item'):
                path = item.find('image').text
                picture_url = 'https://images.lider.cl/wmtcl?source=url%5B{}' \
                              '%5D&sink'.format(path)
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
            cell_plan_name=None,
            cell_monthly_payment=None,
            picture_urls=picture_urls
        )

        return [p]
