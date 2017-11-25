import json

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Sodimac(Store):
    @classmethod
    def categories(cls):
        return [
            'WashingMachine',
            'Refrigerator',
            'Oven',
            'VacuumCleaner',
            'Lamp',
            'Television',
            'Notebook',
            'LightProjector',
            'AirConditioner',
            'WaterHeater',
            'Tablet',
            'SpaceHeater',
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['scat112555/Lavadoras', 'WashingMachine'],  # Lavadoras
            ['cat1590057/Lavadoras-secadoras', 'WashingMachine'],
            ['scat114994/Secadoras', 'WashingMachine'],  # Secadoras
            ['scat112543/Freezer', 'Refrigerator'],  # Freezer
            ['scat114992/No-Frost', 'Refrigerator'],  # No Frost
            ['scat535116/Side-by-Side', 'Refrigerator'],  # Side by Side
            ['scat114991/Frio-Directo', 'Refrigerator'],  # Frio directo
            ['scat112545/Frigobar', 'Refrigerator'],  # Frigobares
            ['cat4850051/Aspiradoras-portatiles', 'VacuumCleaner'],
            # Aspiradoras
            ['cat1580015/Hornos-Electricos', 'Oven'],  # Hornos electricos
            ['scat112547/Microondas', 'Oven'],  # Microondas
            ['cat360045/Ampolletas-LED', 'Lamp'],  # Ampolletas LED
            ['cat3810002/Televisores', 'Television'],  # Televisores
            ['cat3390002/Notebook', 'Notebook'],  # Notebooks
            ['cat2930160/Reflectores-LED', 'LightProjector'],  # Proyectores
            ['scat100321/Aire-Acondicionado', 'AirConditioner'],  # AC
            ['scat663002/Calefont-tiro-natural', 'WaterHeater'],
            ['cat2080050/Calefont-tiro-forzado', 'WaterHeater'],
            ['scat923316/Termos-electricos-hogar', 'WaterHeater'],
            ['scat918650/Calderas', 'WaterHeater'],
            ['cat3620002/Tablet', 'Tablet'],
            ['scat583461/Estufas-Toyotomi', 'SpaceHeater'],
            # ['scat299492/Estufas-a-Gas', 'SpaceHeater'],
            ['scat411008/Estufas-a-Parafina', 'SpaceHeater'],
            ['cat1560069/Termoventiladores', 'SpaceHeater'],
            ['cat1560012/Estufas-Far-Infrared', 'SpaceHeater'],
            ['cat1560071/Convectores', 'SpaceHeater'],
            ['cat1590078/Estufas-Tiro-Forzado', 'SpaceHeater'],
            ['scat301608/Estufas-a-Lena', 'SpaceHeater'],
            ['cat3870010/Smartphones', 'Cell'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 0

            while True:
                url = 'http://www.sodimac.cl/sodimac-cl/category/{}?No={}' \
                      ''.format(category_path, page)
                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                mosaic_divs = soup.findAll('div', 'informationContainer')

                if not mosaic_divs:
                    if page == 0:
                        raise Exception('No products for {}'.format(url))
                    break

                for div in mosaic_divs:
                    product_url = 'http://www.sodimac.cl' + \
                                  div.find('a')['href']
                    product_url = product_url.replace(' ', '')
                    product_urls.append(product_url)
                page += 16

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        response = session.get(url)
        if 'empty=true' in response.url:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        sku = soup.find('input', {'id': 'currentProductId'})['value'].strip()

        pricing_container = soup.find('div', {'id': 'JsonArray'})

        if soup.find('div', {'id': 'JsonArray'}):
            pricing_json = json.loads(pricing_container.text)[0]

            normal_price = Decimal(pricing_json['INTERNET'])

            if 'CMR' in pricing_json:
                offer_price = Decimal(pricing_json['CMR'])
                if offer_price > normal_price:
                    offer_price = normal_price
            else:
                offer_price = normal_price

            name = '{} {}'.format(pricing_json.get('brand', ''),
                                  pricing_json['name']).strip()

            stock_regex = '{}=(\d+)'.format(sku)
            stock = int(re.search(stock_regex,
                                  pricing_json['stockLevel']).groups()[0])
        else:
            stock = 0
            normal_price = Decimal(remove_words(
                soup.find('p', 'price').text.split('\xa0')[0]))
            offer_price = normal_price

            model = soup.find('h1', 'name').text
            brand = soup.find('h2', 'brand').text
            name = u'{} {}'.format(brand, model)

        description = '\n\n'.join([html_to_markdown(str(panel)) for panel in
                                   soup.findAll('section', 'prod-car')])

        # Pictures

        pictures_resource_url = 'http://sodimac.scene7.com/is/image/' \
                                'SodimacCL/{}?req=set,json'.format(sku)
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      session.get(pictures_resource_url).text).groups()[0])

        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https://sodimac.scene7.com/is/image/{}?scl=1.0' \
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
