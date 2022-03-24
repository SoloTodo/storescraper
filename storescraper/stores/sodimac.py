import json
import logging
import random
import re

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import OVEN, REFRIGERATOR, DISH_WASHER, \
    WASHING_MACHINE, AIR_CONDITIONER, SPACE_HEATER, WATER_HEATER, \
    VACUUM_CLEANER, NOTEBOOK, PRINTER, TABLET, MONITOR, MOTHERBOARD, MOUSE, \
    CELL, WEARABLE, TELEVISION, VIDEO_GAME_CONSOLE, STEREO_SYSTEM, \
    HEADPHONES, EXTERNAL_STORAGE_DRIVE, UPS
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown, CF_REQUEST_HEADERS


class Sodimac(Store):
    @classmethod
    def categories(cls):
        return [
            WASHING_MACHINE,
            REFRIGERATOR,
            OVEN,
            TELEVISION,
            NOTEBOOK,
            AIR_CONDITIONER,
            WATER_HEATER,
            TABLET,
            SPACE_HEATER,
            CELL,
            HEADPHONES,
            STEREO_SYSTEM,
            VIDEO_GAME_CONSOLE,
            MONITOR,
            UPS,
            PRINTER,
            DISH_WASHER,
            VACUUM_CLEANER,
            MOTHERBOARD,
            MOUSE,
            WEARABLE,
            EXTERNAL_STORAGE_DRIVE
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        entries = {}
        entries.update(cls.discover_entries_for_category_old(
            category, extra_args))
        entries.update(cls.discover_entries_for_category_new(
            category, extra_args))
        return entries

    @classmethod
    def discover_entries_for_category_old(cls, category, extra_args=None):
        category_paths = [
            ['cat8720053', [OVEN],
             'Electrohogar y Climatización > Electrodomésticos de Cocina > '
             'Microondas, Hornos y Tostadores', 1],
            ['scat112547', [OVEN],
             'Electrohogar y Climatización > Electrodomésticos de Cocina > '
             'Microondas, Hornos y Tostadores > Microondas', 1],
            ['cat1580015', [OVEN],
             'Electrohogar y Climatización > Electrodomésticos de Cocina > '
             'Microondas, Hornos y Tostadores > Hornos Eléctricos', 1],
            ['scat112552', [OVEN],
             'Electrohogar y Climatización > Encimeras, Hornos y Campanas > '
             'Hornos Empotrables', 1],
            ['scat112558', [DISH_WASHER],
             'Electrohogar y Climatización > Línea Blanca > '
             'Lavavajillas', 1],
            ['scat112543', [REFRIGERATOR],
             'Electrohogar y Climatización > Línea Blanca > '
             'Freezer y Congeladores', 1],
            ['scat112555', [WASHING_MACHINE],
             'Electrohogar y Climatización > Línea Blanca > Lavadoras', 1],
            ['scat114994', [WASHING_MACHINE],
             'Electrohogar y Climatización > Línea Blanca > '
             'Secadoras de Ropa', 1],
            ['cat1590057', [WASHING_MACHINE],
             'Electrohogar y Climatización > Línea Blanca > '
             'Lavadoras y Secadoras', 1],
            ['cat4780002', [AIR_CONDITIONER],
             'Electrohogar y Climatización > Aire Acondicionado y Ventilación'
             ' > Aires Acondicionados', 1],
            ['scat963231', [SPACE_HEATER],
             'Electrohogar y Climatización > Calefacción > Estufas', 1],
            ['scat922142', [WATER_HEATER],
             'Electrohogar y Climatización > Calefacción > '
             'Calefont y Termos', 1],
            ['scat112378', [VACUUM_CLEANER],
             'Electrohogar y Climatización > Electrodomésticos del Hogar > '
             'Aspiradoras', 1],
            ['cat3390002', [NOTEBOOK],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Computación > Notebooks', 1],
            ['cat3550016', [PRINTER],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Computación > Impresoras', 1],
            ['cat3620002', [TABLET],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Computación > Tablets', 1],
            ['cat3810003', [MONITOR],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Computación > Monitores LED', 1],
            ['scat913767', [MOTHERBOARD],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Computación > Accesorios Computación', 1],
            ['cat4850238', [MOUSE],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Computación > Computación Gamer', 1],
            ['cat8350007', [MOUSE],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Computación > Mouse y Teclados', 1],
            ['cat3870010', [CELL],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Celulares y Telefonía > Celulares Smartphones', 1],
            ['cat3870009', [WEARABLE],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Celulares y Telefonía > Smartwatch', 1],
            ['cat3810002', [TELEVISION],
             'Televisores LED', 1],
            ['cat3890001', [VIDEO_GAME_CONSOLE],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Gamer > Consolas de Videojuegos', 1],
            ['scat913770', [STEREO_SYSTEM],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Audio > Equipos de Música', 1],
            ['cat3870001', [HEADPHONES],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Audio > Audífonos', 1],
            ['scat913770', [STEREO_SYSTEM],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Audio > Parlantes bluetooth', 1],
            ['cat3970001', [EXTERNAL_STORAGE_DRIVE],
             'Electrohogar y Climatización > Tecnología y TV > '
             'Almacenamiento externo', 1],
            ['cat2940090', [UPS],
             'Construcción y Ferretería > Electricidad > '
             'Transformadores Eléctricos y UPS > Baterías de respaldo', 1],
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
    def discover_entries_for_category_new(cls, category, extra_args=None):
        from storescraper.stores import Falabella

        category_paths = [
            ['cat3205', [REFRIGERATOR],
             'Home > Sodimac > Electrohogar-Línea Blanca > Refrigeradores', 1],
            ['cat4074', [REFRIGERATOR],
             'Home > Sodimac > Electrohogar-Línea Blanca > Refrigeradores > '
             'No Frost',
             1],
            ['cat4048', [REFRIGERATOR],
             'Home > Sodimac > Electrohogar-Línea Blanca > Refrigeradores > '
             'Freezers',
             1],
            ['cat4036', [REFRIGERATOR],
             'Home > Sodimac > Electrohogar-Línea Blanca > Refrigeradores > '
             'Frío directo',
             1],
            ['cat4091', [REFRIGERATOR],
             'Home > Sodimac > Refrigeración-Side by Side', 1],
            ['cat4049', [REFRIGERATOR],
             'Home > Sodimac > Electrohogar-Línea Blanca > Refrigeradores > '
             'Frigobar',
             1],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = CF_REQUEST_HEADERS['User-Agent']
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            category_product_urls = Falabella._get_product_urls(
                session, category_id, 'sodimac')

            for idx, url in enumerate(category_product_urls):
                product_entries[url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

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
        from storescraper.stores import Falabella
        print(url)

        session = session_with_proxy(extra_args)

        separator = '&' if '?' in url else '?'

        r_url = url + separator + "rnd={}".format(random.randint(0, 1000))
        print(r_url)

        try:
            response = session.get(r_url, timeout=30)
        except UnicodeDecodeError:
            return []

        if response.status_code in [404]:
            return []

        if 'falabella.com' in response.url:
            ps = Falabella.products_for_url(url, category, extra_args)
            for p in ps:
                p.store = cls.__name__
                p.url = url
                if p.seller in ['SODIMAC_CHILE', 'SODIMAC']:
                    p.seller = None
            return ps

        soup = BeautifulSoup(response.text, 'html.parser')

        if soup.find('div', {'id': 'testId-product-outofstock'}):
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
