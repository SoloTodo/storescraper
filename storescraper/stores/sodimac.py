import json
import random
import re

from collections import defaultdict
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
            'Headphones',
            'StereoSystem',
            'Wearable',
            'VideoGameConsole',
            'Monitor',
            'Ups',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['scat112555/Lavadoras', ['WashingMachine'],
             'Sodimac.com > Línea Blanca > Lavadoras', 1],
            ['cat1590057/Lavadoras-secadoras', ['WashingMachine'],
             'Sodimac.com > Lavadoras y Secadoras > Lavadoras secadoras', 1],
            ['scat114994/Secadoras', ['WashingMachine'],
             'Sodimac.com > Lavadoras y Secadoras > Secadoras', 1],
            ['scat112543/Freezer', ['Refrigerator'],
             'Sodimac.com > Refrigeradores > Freezer', 1],
            ['scat114992/No-Frost', ['Refrigerator'],
             'Sodimac.com > Refrigeradores > Refrigeradores No Frost', 1],
            ['scat535116/Side-by-Side', ['Refrigerator'],
             'Sodimac.com > Refrigeradores > Refrigeradores Side by Side', 1],
            ['scat114991/Frio-Directo', ['Refrigerator'],
             'Sodimac.com > Refrigeradores > Refrigeradores Frío Directo', 1],
            ['scat112545/Frigobar', ['Refrigerator'],
             'Sodimac.com > Refrigeradores > Frigobar', 1],
            ['cat4850051/Aspiradoras-portatiles', ['VacuumCleaner'],
             'Sodimac.com > Aspiradoras > Aspiradoras portátiles', 1],
            ['cat1580015/Hornos-Electricos', ['Oven'],
             'Sodimac.com > Microondas y Hornos Eléctricos > '
             'Hornos Eléctricos', 1],
            ['scat112547/Microondas', ['Oven'],
             'Sodimac.com > Microondas y Hornos Eléctricos > Microondas', 1],
            ['cat360045/Ampolletas-LED', ['Lamp'],
             'Sodimac.com > Ampolletas y Tubos > Ampolletas y Tubos LED', 1],
            ['cat3810002/Televisores', ['Television'],
             'Sodimac.com > Tv y Video > Televisores', 1],
            ['cat3810003/Monitores-LED', ['Monitor'],
             'Sodimac.com > Tv y Video > Monitores LED', 1],
            ['cat3390002/Notebook', ['Notebook'],
             'Sodimac.com > Computación > Notebooks', 1],
            ['cat2930160/Reflectores-LED', ['LightProjector'],
             'Sodimac.com > Iluminación Comercial LED > Reflectores LED', 1],
            ['cat4780002/Aires-Acondicionados-Split', ['AirConditioner'],
             'Sodimac.com > Calefacción > Aires Acondicionados Split', 1],
            ['scat663002/Calefont-tiro-natural', ['WaterHeater'],
             'Sodimac.com > Calefont y Termos > Calefont tiro natural', 1],
            ['cat2080050/Calefont-tiro-forzado', ['WaterHeater'],
             'Sodimac.com > Calefont y Termos > Calefont tiro forzado', 1],
            ['scat923316/Termos-y-Calderas', ['WaterHeater'],
             'Sodimac.com > Calefont y Termos > Termos y Calderas', 1],
            ['cat3620002/Tablets', ['Tablet'],
             'Sodimac.com > Computación > Tablets', 1],
            ['scat583461/Estufas-Toyotomi', ['SpaceHeater'],
             'Sodimac.com > Estufas > Estufas Toyotomi', 1],
            ['scat299492/Estufas-a-Gas', ['SpaceHeater'],
             'Sodimac.com > Estufas > Estufas a Gas', 1],
            ['scat411008/Estufas-a-Parafina', ['SpaceHeater'],
             'Sodimac.com > Estufas > Estufas a Parafina', 1],
            # ['cat1560069/Termoventiladores', ['SpaceHeater']],
            # ['cat1560012/Estufas-Far-Infrared', ['SpaceHeater']],
            # ['cat1560071/Convectores', ['SpaceHeater']],
            ['cat1590078/Estufas-Tiro-Forzado', ['SpaceHeater'],
             'Sodimac.com > Estufas > Estufas Tiro Forzado', 1],
            ['scat301608/Estufas-a-Lena', ['SpaceHeater'],
             'Sodimac.com > Estufas > Estufas a Leña', 1],

            ['cat3870010/Smartphones', ['Cell'],
             'Sodimac.com > Celulars y Telefonía > Smartphones', 1],

            ['cat3870001/Audifonos', ['Headphones'],
             'Sodimac.com > Tecnología Deportiva > Audífonos', 1],

            ['scat913770/Equipos-de-Musica', ['StereoSystem'],
             'Sodimac.com > Tecnología y Seguridad > Equipos de Música', 1],
            # ['cat4850257/Home-Theater-y-Soundbars', ['StereoSystem']],
            ['cat8350012/Parlantes-bluetooth', ['StereoSystem'],
             'Sodimac.com > Audio > Parlantes bluetooth', 1],
            # ['cat4850400/Parlantes-y-Karaokes', ['StereoSystem']],
            ['cat8350014/Tornamesas', ['StereoSystem'],
             'Sodimac.com > Audio > Tornamesas', 1],
            ['cat3870009/Wearables', ['Wearable'],
             'Sodimac.com > Tecnología Deportiva > SmartWatch', 1],
            ['cat3890001/Consolas-de-videojuegos', ['VideoGameConsole'],
             'Sodimac.com > Gamer > Consolas de videojuegos', 1],
            ['cat2940090/Baterias-de-respaldo', ['Ups'],
             'Sodimac.com > Transformadores Eléctricos y UPS > '
             'Baterías de respaldo', 1],
        ]

        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 0
            current_position = 1

            while True:
                url = 'https://www.sodimac.cl/sodimac-cl/category/{}?No={}' \
                      '&rnd={}'.format(category_path, page,
                                       random.randint(0, 100))
                print(url)

                response = session.get(url, timeout=30)

                if '/product/' in response.url:
                    product_entries[response.url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': current_position
                    })
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                mosaic_divs = soup.findAll('section', 'jq-item')

                if not mosaic_divs:
                    if page == 0:
                        raise Exception('No products for {}'.format(url))
                    break

                for div in mosaic_divs:
                    product_url = 'https://www.sodimac.cl/sodimac-cl/' \
                                  'product/' + div['data']
                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': current_position
                    })
                    current_position += 1
                page += 16

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        page = 0

        while True:
            url = 'https://www.sodimac.cl/sodimac-cl/search/?No={}&Ntt={}'\
                .format(page, keyword)

            print(url)

            response = session.get(url, timeout=30)

            if '/product/' in response.url:
                product_urls.append(response.url)
                break

            soup = BeautifulSoup(response.text, 'html.parser')

            mosaic_divs = soup.findAll('section', 'jq-item')

            if not mosaic_divs:
                break

            for div in mosaic_divs:
                product_url = 'https://www.sodimac.cl/sodimac-cl/' \
                              'product/' + div['data']
                product_urls.append(product_url)

                if len(product_urls) == threshold:
                    return product_urls

            page += 16

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        response = session.get(url, timeout=30)

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        if soup.find('p', 'sinStock-online-p-SEO'):
            return []

        sku = soup.find('input', {'id': 'currentProductId'})['value'].strip()
        key = soup.find('input', {'id': 'currentSkuId'})['value'].strip()

        pricing_container = soup.find('div', {'id': 'JsonArray'})

        if soup.find('div', {'id': 'JsonArray'}):
            pricing_json = json.loads(pricing_container.text)[0]

            if 'EVENTO' in pricing_json:
                normal_price = Decimal(pricing_json['EVENTO'])
            elif 'MASBAJO' in pricing_json:
                normal_price = Decimal(pricing_json['MASBAJO'])
            elif 'INTERNET' in pricing_json:
                normal_price = Decimal(pricing_json['INTERNET'])
            else:
                return []

            if 'CMR' in pricing_json:
                offer_price = Decimal(pricing_json['CMR'])
                if offer_price > normal_price:
                    offer_price = normal_price
            else:
                offer_price = normal_price

            name = '{} {}'.format(pricing_json.get('brand', ''),
                                  pricing_json['name']).strip()

            stock_regex = r'{}=(\d+)'.format(key)
            stock_text = re.search(stock_regex,
                                   pricing_json['stockLevel']).groups()[0]
            stock = int(stock_text)
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

        pictures_resource_url = 'https://sodimac.scene7.com/is/image/' \
                                'SodimacCL/{}?req=set,json'.format(sku)
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      session.get(pictures_resource_url,
                                  timeout=30).text).groups()[0])

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
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
