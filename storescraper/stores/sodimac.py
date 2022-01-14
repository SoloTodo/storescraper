import json
import logging
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
            'VideoGameConsole',
            'Monitor',
            'Ups',
            'Printer',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['scat112555', ['WashingMachine'],
             'Lavadoras y Secadoras > Lavadoras', 1],
            ['cat1590057', ['WashingMachine'],
             'Línea Blanca > Lavadoras y Secadoras', 1],
            ['scat114994', ['WashingMachine'],
             'Lavadoras y Secadoras > Secadoras', 1],
            ['scat112543', ['Refrigerator'],
             'Refrigeradores > Freezer', 1],
            ['scat114992', ['Refrigerator'],
             'Refrigeradores > Refrigeradores No Frost', 1],
            ['scat535116', ['Refrigerator'],
             'Refrigeradores > Refrigeradores Side by Side', 1],
            ['scat114991', ['Refrigerator'],
             'Refrigeradores > Refrigeradores Frío Directo', 1],
            ['scat112545', ['Refrigerator'],
             'Refrigeradores > Frigobares y Cavas de Vino', 1],
            ['cat4850343', ['Oven'],
             'Cocinas, Hornos y Campanas > Microondas y Hornos Eléctricos', 1],
            ['scat112547', ['Oven'],
             'Microondas y Hornos Eléctricos > Microondas', 1],
            ['cat1580015', ['Oven'],
             'Microondas y Hornos Eléctricos  > Hornos Eléctricos', 1],
            ['cat3810002', ['Television'],
             'Tv y Video > Televisores LED', 1],
            ['cat3810003', ['Monitor'],
             'Tv y Video > Monitores LED', 1],
            ['cat3390002', ['Notebook'],
             'Computación > Notebooks', 1],
            ['cat4780002', ['AirConditioner'],
             'Aire Acondicionado y Ventilación > '
             'Aires Acondicionados Split', 1],
            ['cat4780001', ['AirConditioner'],
             'Aire Acondicionado y Ventilación > '
             'Aires Acondicionados Portátiles', 1],
            ['scat663002/Calefont-tiro-natural', ['WaterHeater'],
             'Sodimac.com > Calefont y Termos > Calefont tiro natural', 1],
            ['cat2080050/Calefont-tiro-forzado', ['WaterHeater'],
             'Sodimac.com > Calefont y Termos > Calefont tiro forzado', 1],
            ['scat923316/Termos-y-Calderas', ['WaterHeater'],
             'Sodimac.com > Calefont y Termos > Termos y Calderas', 1],
            ['scat299492', ['SpaceHeater'],
             'Estufas > Estufas a Gas', 1],
            ['scat411008', ['SpaceHeater'],
             'Estufas > Estufas a Parafina', 1],
            ['scat301608', ['SpaceHeater'],
             'Estufas > Estufas a Leña', 1],
            ['scat299482', ['SpaceHeater'],
             'Estufas > Estufas a Pellet', 1],
            # ['scat963234', ['SpaceHeater'],
            #  'Estufas > Estufas Eléctricas', 1],
            ['cat3870010', ['Cell'],
             'Celulares y Telefonía > Smartphones', 1],
            ['cat8930005', ['Cell'],
             'Celulares y Telefonía > Celulares Reacondicionados', 1],
            ['cat3870001', ['Headphones'],
             'Tecnología Deportiva > Audífonos', 1],
            ['scat913770', ['StereoSystem'],
             'Tecnología y TV > Equipos de Música', 1],
            # ['cat8350012', ['StereoSystem'],
            #  'Audio > Parlantes bluetooth', 1],
            ['cat3890001', ['VideoGameConsole'],
             'Gamer > Consolas de videojuegos', 1],
            ['cat2940090', ['Ups'],
             'Transformadores Eléctricos y UPS > Baterías de respaldo', 1],
            ['cat3550016', ['Printer'],
             'Especiales > Tecno indispensables > Impresoras', 1],
        ]

        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1
            current_position = 1
            print(category_id)

            while True:
                url = 'https://www.sodimac.cl/s/search/v1/socl/category/' \
                      'products?priceGroup=96&zone=130617&currentpage={}&' \
                      'sortBy=_score,desc&categoryId={}' \
                    .format(page, category_id)

                response = session.get(url, timeout=30)

                # Page 3 of televisores LED returns 500 for some reason
                if response.status_code == 500:
                    break

                data = json.loads(response.text)['data']

                products = data['results']

                if not products:
                    if page == 1:
                        logging.warning('No products for {}'.format(url))
                    break

                for product in products:
                    product_id = product['productId']
                    product_url = 'https://www.sodimac.cl/' \
                                  'sodimac-cl/product/{}'.format(product_id)

                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': current_position
                    })
                    current_position += 1

                page += 1

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        page = 0

        while True:
            url = 'https://www.sodimac.cl/sodimac-cl/search/?No={}&Ntt={}' \
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
        print(url)
        session = session_with_proxy(extra_args)
        r_url = url + "?rnd={}".format(random.randint(0, 1000))
        print(r_url)
        response = session.get(r_url, timeout=30)

        if response.status_code in [404]:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        if soup.find('p', 'sinStock-online-p-SEO'):
            return []

        sku_container = soup.find('input', {'id': 'currentProductId'})

        if sku_container:
            print('OLD')
            return cls._old_products_for_url(url, session, soup, category)
        else:
            print('NEW')
            return cls._new_products_for_url(url, session, soup, category)

    @classmethod
    def _old_products_for_url(cls, url, session, soup, category):
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

        if 'reacondicionado' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

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
            picture_urls=picture_urls,
            condition=condition
        )

        return [p]

    @classmethod
    def _new_products_for_url(cls, url, session, soup, category):
        sku = soup.find(
            'div', 'product-cod').text.replace('Código', '').strip()
        name = soup.find('h1', 'product-title').text.strip()
        brand = soup.find('div', 'product-brand').text.strip()
        name = "{} {}".format(brand, name)

        if not soup.find('div', 'normal'):
            return []

        normal_price = Decimal(
            soup.find('div', 'normal').find('div', 'price').text
                .replace('c/u', '').replace('$', '').replace('.', '')
                .replace('Normal', '').replace('pack', '').replace('caja', '')
                .strip())

        offer_price_container = soup.find('div', 'cmr')
        offer_price = None

        if offer_price_container and \
                offer_price_container.find('div', 'price'):
            offer_price = Decimal(
                soup.find('div', 'cmr').find('div', 'price').text
                    .replace('c/u', '').replace('$', '').replace('.', '')
                    .replace('caja', '')
                    .strip())
        if not offer_price:
            data_json = json.loads(
                soup.find("script", {"id": "__NEXT_DATA__"}).text)
            offer_price = Decimal(
                    data_json['props']['pageProps']['productProps']['result'][
                        'variants'][0]['price'][0]['price'].replace('.', ''))
            if data_json['props']['pageProps']['productProps']['result'][
                    'variants'][0]['price'][0]['type'] == 'EVENT':
                normal_price = offer_price

        if not offer_price:
            offer_price = normal_price

        add_button = soup.find('button', {'id': 'testId-btn-add-to-cart'})

        if add_button:
            stock = -1
        else:
            stock = 0

        pictures_resource_url = 'https://sodimac.scene7.com/is/image/' \
                                'SodimacCL/{}?req=set,json'.format(sku)
        pictures_response = session.get(pictures_resource_url).text
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      pictures_response).groups()[0])

        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https://sodimac.scene7.com/is/image/{}?' \
                          'wid=1500&hei=1500&qlt=70' \
                .format(picture_entry['i']['n'])
            picture_urls.append(picture_url)

        description = html_to_markdown(str(soup.find('div', 'product-info')))

        if 'reacondicionado' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

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
            picture_urls=picture_urls,
            condition=condition,
            # seller=seller
        )

        return [p]
