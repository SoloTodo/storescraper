import json

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Easy(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'Television',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'StereoSystem',
            'OpticalDiskPlayer',
            'Lamp',
            'LightTube'
            'LightProjector',
            'WaterHeater',
            'SpaceHeater',
            'AirConditioner',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['electrohogar/refrigeracion/frio-directo', 'Refrigerator'],
            ['electrohogar/refrigeracion/no-frost', 'Refrigerator'],
            ['electrohogar/refrigeracion/freezer', 'Refrigerator'],
            ['electrohogar/refrigeracion/frigobar', 'Refrigerator'],
            ['electrohogar/refrigeracion/side-by-side', 'Refrigerator'],
            # ['electrohogar/tecnologia/televisores', 'Television'],
            ['electrohogar/cocina-electrohogar/hornos-electricos', 'Oven'],
            ['electrohogar/cocina-electrohogar/hornos-empotrables', 'Oven'],
            ['electrohogar/cocina-electrohogar/microondas', 'Oven'],
            ['electrohogar/electrodomesticos/aspiradoras', 'VacuumCleaner'],
            ['electrohogar/lavado-y-secado/lavadoras', 'WashingMachine'],
            ['electrohogar/lavado-y-secado/lavadora-secadora',
             'WashingMachine'],
            ['electrohogar/lavado-y-secado/secadoras', 'WashingMachine'],
            ['electrohogar/tecnologia/reproductores', 'OpticalDiskPlayer'],
            ['iluminacion/iluminación-led', 'Lamp'],
            ['iluminacion-de-exterior/reflectores-exterior', 'LightProjector'],
            ['electrohogar/calefones-y-termos/calefont-gas-licuado',
             'WaterHeater'],
            ['electrohogar/calefones-y-termos/calefont-gas-natural',
             'WaterHeater'],
            ['electrohogar/calefones-y-termos/termos', 'WaterHeater'],
            # ['electrohogar/calefaccion/calefactores-a-leña', 'SpaceHeater'],
            ['electrohogar/calefaccion/estufas-infrarrojas', 'SpaceHeater'],
            ['electrohogar/calefaccion/estufas-a-gas', 'SpaceHeater'],
            # ['electrohogar/calefaccion/estufas-a-parafina', 'SpaceHeater'],
            # ['electrohogar/calefaccion/chimeneas-electricas', 'SpaceHeater'],
            ['electrohogar/calefaccion/paneles-calefactores', 'SpaceHeater'],
            # ['electrohogar/calefaccion/calefactores-a-pellet',
            # 'SpaceHeater'],
            ['electrohogar/calefaccion/termoventiladores', 'SpaceHeater'],
            ['especial-hola-invierno/calefaccion/estufas-electrica',
             'SpaceHeater'],
            ['electrohogar/climatizacion/aire-acondicionado-portatil',
             'AirConditioner'],
            ['electrohogar/climatizacion/aire-acondicionado-split',
             'AirConditioner'],
            ['audio', 'StereoSystem'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.easy.cl/es/easy-chile/{}'.format(
                category_path)
            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            page_id = soup.find('meta', {'name': 'pageId'})['content']

            category_url = 'http://www.easy.cl/ProductListingView?storeId=' \
                           '10151&resultsPerPage=1000&categoryId=' + page_id

            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            divs = soup.findAll('div', 'product')

            if not divs:
                raise Exception('Empty category: ' + category_path)

            for div in divs:
                product_url = div.findAll('a')[1]['href']
                product_path = product_url.split('/')[-1]
                product_url = 'https://www.easy.cl/es/easy-chile/' + \
                    product_path
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('span', 'tit_current')

        if not name:
            return []

        name = name.text.strip()

        sku = soup.find('meta', {'name': 'pageIdentifier'})['content'].strip()
        description = html_to_markdown(str(soup.find('div', 'box_2')))

        product_id = soup.find('meta', {'name': 'pageId'})['content']

        stock_url = 'https://www.easy.cl/' \
            'AjaxShoppingActionsRefreshView?productId={}&' \
            'storeId=10151'.format(product_id)

        stock_soup = BeautifulSoup(session.get(stock_url).text, 'html.parser')

        if stock_soup.find('div', text='Sin stock para compra online'):
            stock = 0
        else:
            stock = -1

        soup = soup.find('div', 'section_price')

        normal_price = soup.find('span', 'inetprice')
        normal_price = Decimal(remove_words(normal_price.string))

        cencosud_price_container = soup.find(
            'div', {'class': 'especial pricevisible'})
        if cencosud_price_container:
            offer_price = cencosud_price_container.find('span').string
            offer_price = Decimal(remove_words(offer_price))
        else:
            offer_price = normal_price

        # Pictures

        pictures_id = sku[:-1]

        pictures_resource_url = 'https://s7d2.scene7.com/is/image/' \
                                'EasySA/{}?req=set,json,UTF-8'.format(
                                    pictures_id)
        pictures_content = re.search(r's7jsonResponse\((.+),""\);',
                                     session.get(pictures_resource_url).text)

        if pictures_content:
            picture_urls = []
            pictures_json = json.loads(pictures_content.groups()[0])
            picture_entries = pictures_json['set']['item']
            if not isinstance(picture_entries, list):
                picture_entries = [picture_entries]

            for picture_entry in picture_entries:
                if 'i' not in picture_entry:
                    continue
                picture_url = 'https://s7d2.scene7.com/is/image/{}?' \
                              'scl=1.0'.format(picture_entry['i']['n'])
                picture_urls.append(picture_url)
        else:
            picture_urls = None

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
