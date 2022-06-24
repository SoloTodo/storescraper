import logging
import re
import json
from datetime import datetime

import validators
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR
from storescraper.store import Store
from storescraper.product import Product
from storescraper.flixmedia import flixmedia_video_urls
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper import banner_sections as bs


class Ripley(Store):
    preferred_products_for_url_concurrency = 3

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'Stove',
            'DishWasher',
            # 'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'StereoSystem',
            'OpticalDiskPlayer',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            # 'MemoryCard',
            'Projector',
            'VideoGameConsole',
            'Monitor',
            'AllInOne',
            'AirConditioner',
            # 'WaterHeater',
            # 'SolidStateDrive',
            'SpaceHeater',
            'Wearable',
            # 'Mouse',
            # 'Keyboard',
            # 'KeyboardMouseCombo',
            'Headphones',
            'Ram',
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        return [category]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        # This implementation of products_for_url is botched to obtain the
        # products directly from the PLP page of Ripley because we can't
        # make too many requests to the Ripley website. Therefore "url" is
        # just the name of the category and ignored

        # This method may be called as part of the keyword search functionality
        # of the library. We patch it by detecting this call and calling
        # a function that actually uses the URL PDP page of the product.
        if extra_args and extra_args.get('source', None) == 'keyword_search':
            product = cls._assemble_full_product(
                url, category, extra_args)
            if not product:
                return []
            return [product]

        category_paths = [
            ['tecno/computacion/notebooks', ['Notebook'],
             'Tecno > Computación > Notebooks', 1],
            ['tecno/computacion/notebooks-gamer', ['Notebook'],
             'Tecno > Computación > Notebooks gamer', 1],
            ['tecno/computacion/tablets-y-e-readers', ['Tablet'],
             'Tecno > Computación > Tablets y E-readers', 1],
            ['tecno/impresoras-y-tintas/impresoras', ['Printer'],
             'Tecno > Computación > Impresoras', 1],
            ['tecno/computacion/almacenamiento',
             ['UsbFlashDrive', 'ExternalStorageDrive'],
             'Tecno > Computación > Almacenamiento', 0.5],
            ['tecno/computacion/pc-all-in-one', ['AllInOne'],
             'Tecno > Computación > PC/All in one', 1],
            ['tecno/computacion/proyectores-y-monitores',
             ['Monitor', 'Projector'],
             'Tecno > Computación > Proyectores y monitores', 0.5],
            ['tecno/computacion-gamer/componentes-pc', ['Ram'],
             'Tecno > Computación Gamer > Componentes', 1],
            ['tecno/computacion-gamer/monitores', ['Monitor'],
             'Tecno > Computación Gamer > Monitores', 1],
            ['tecno/television', ['Television'],
             'Tecno > Televisión', 1],
            ['tecno/television/smart-tv', ['Television'],
             'Tecno > Televisión > Smart TV', 1],
            ['tecno/television/ultra-hd-4k', ['Television'],
             'Tecno > Televisión > Ultra HD 4K', 1],
            ['tecno/television/premium-tv-y-8k', ['Television'],
             'Tecno > Televisión > Premium y 8K', 1],
            ['tecno/television/hd-y-full-hd', ['Television'],
             'Tecno > Televisión > HD y Full HD', 1],
            ['electro/refrigeracion', ['Refrigerator'],
             'Electro > Refrigeración', 1],
            ['electro/refrigeracion/side-by-side', ['Refrigerator'],
             'Electro > Refrigeración > Side by Side', 1],
            ['electro/refrigeracion/refrigeradores', ['Refrigerator'],
             'Electro > Refrigeración > Refrigeradores', 1],
            ['electro/refrigeracion/freezers-y-congeladores', ['Refrigerator'],
             'Electro > Refrigeración > Freezers y congeladores', 1],
            ['electro/refrigeracion/frigobar', ['Refrigerator'],
             'Electro > Refrigeración > Frigobar', 1],
            # ['electro/refrigeracion/door-in-door', ['Refrigerator'],
            #  'Electro > Refrigeración > Door in Door', 1],
            ['electro/cocina/cocinas', ['Stove'],
             'Electro > Cocina > Cocinas', 1],
            ['electro/electrodomesticos/hornos-y-microondas', ['Oven'],
             'Electro > Electrodomésticos > Hornos y Microondas', 1],
            ['electro/cocina/lavavajillas', ['DishWasher'],
             'Electro > Cocina > Lavavajillas', 1],
            ['electro/aseo/aspiradoras-y-enceradoras', ['VacuumCleaner'],
             'Electro > Aseo > Aspiradoras y enceradoras', 1],
            ['electro/lavanderia', ['WashingMachine'],
             'Electro > Lavandería', 1],
            ['electro/lavanderia/lavadoras', ['WashingMachine'],
             'Electro > Lavandería > Lavadoras', 1],
            ['electro/lavanderia/secadoras', ['WashingMachine'],
             'Electro > Lavandería > Secadoras', 1],
            ['electro/lavanderia/lavadora-secadora', ['WashingMachine'],
             'Electro > Lavandería > Lavadora-secadora', 1],
            ['electro/lavanderia/doble-carga', ['WashingMachine'],
             'Electro > Lavandería > Doble carga', 1],
            ['tecno/celulares/iphone', ['Cell'],
             'Tecno > Telefonía > iPhone', 1],
            ['tecno/celulares/samsung', ['Cell'],
             'Tecno > Telefonía > Samsung', 1],
            ['tecno/celulares/huawei', ['Cell'],
             'Tecno > Telefonía > Huawei', 1],
            ['tecno/celulares/xiaomi', ['Cell'],
             'Tecno > Telefonía > Xiaomi', 1],
            ['tecno/celulares/motorola', ['Cell'],
             'Tecno > Telefonía > Motorola', 1],
            # ['tecno/celulares/celulares-basicos', ['Cell'],
            #  'Tecno > Telefonía > Básicos', 1],
            ['tecno/audio-y-musica', ['StereoSystem'],
             'Tecno > Audio y Música', 0],
            ['tecno/audio-y-musica/equipos-de-musica', ['StereoSystem'],
             'Tecno > Audio y Música > Equipos de música', 1],
            ['tecno/audio-y-musica/parlantes-bluetooth', ['StereoSystem'],
             'Tecno > Audio y Música > Parlantes Portables', 1],
            ['tecno/audio-y-musica/soundbar-y-home-theater', ['StereoSystem'],
             'Tecno > Audio y Música > Soundbar y Home theater', 1],
            ['tecno/television/bluray-dvd-y-tv-portatiles',
             ['OpticalDiskPlayer'],
             'Tecno > Televisión > Bluray -DVD y TV Portátil', 1],
            ['tecno/playstation/consolas', ['VideoGameConsole'],
             'Tecno > PlayStation > Consolas', 1],
            ['tecno/nintendo/consolas', ['VideoGameConsole'],
             'Tecno > Nintendo > Consolas', 1],
            ['tecno/xbox/consolas', ['VideoGameConsole'],
             'Tecno > Xbox > Consolas', 1],
            ['electro/climatizacion/aire-acondicionado',
             ['AirConditioner'],
             'Electro > Climatización > Ventiladores y aire acondicionado', 1],
            ['electro/climatizacion/purificadores-y-humificadores',
             ['AirConditioner'],
             'Electro > Climatización > Purificadores y humidificadores', 1],
            ['electro/especial-calefaccion',
             ['SpaceHeater'],
             'Electro > Climatización > Estufas y calefactores', 1],
            ['tecno/smartwatches-y-smartbands/garmin', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Garmin', 1],
            ['tecno/smartwatches-y-smartbands/polar', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Polar', 1],
            ['tecno/smartwatches-y-smartbands/apple', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Apple Watch', 1],
            ['tecno/smartwatches-y-smartbands/samsung', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Samsung', 1],
            ['tecno/smartwatches-y-smartbands/huawei', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables > Huawei', 1],
            ['tecno/especial-audifonos', ['Headphones'],
             'Tecno > Audio y Música > Audífonos', 1],
            ['tecno/computacion-gamer/sillas-gamer', [GAMING_CHAIR],
             'Tecno > Computación Gamer > Sillas Gamer', 1]
        ]

        session = session_with_proxy(extra_args)

        if extra_args and 'user-agent' in extra_args:
            session.headers['user-agent'] = extra_args['user-agent']

        fast_mode = extra_args.get('fast_mode', False)
        print('fast_mode', fast_mode)

        url_base = 'https://simple.ripley.cl/{}?page={}'
        product_dict = {}

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1
            position = 1

            while True:
                if page > 200:
                    raise Exception('Page overflow')

                category_url = url_base.format(category_path, page)
                print(category_url)
                response = session.get(category_url, allow_redirects=True,
                                       timeout=60)

                if response.status_code != 200 and page == 1:
                    raise Exception('Invalid section: ' + category_url)

                soup = BeautifulSoup(response.text, 'html.parser')
                products_data = soup.find('script',
                                          {'type': 'application/ld+json'})

                products_soup = soup.find('div', 'catalog-container')

                if not products_data or not products_soup:
                    if page == 1:
                        logging.warning('Empty path: {}'.format(category_url))
                    break

                products_elements = products_soup.findAll(
                    'div', 'ProductItem__Row')

                if not products_elements:
                    products_elements = products_soup.findAll(
                        'a', 'catalog-product-item')

                products_json = json.loads(products_data.text)[
                    'itemListElement']

                assert (len(products_elements) == len(products_json))

                for product_json in products_json:
                    product_element = products_elements[
                        int(product_json['position']) - 1]
                    product_data = product_json['item']

                    brand = product_data.get('brand', '').upper()

                    if brand in ['LG', 'SAMSUNG'] and 'MPM' not in \
                            product_data['sku'] and not fast_mode:
                        # If the product is LG or Samsung and is sold directly
                        # by Ripley (not marketplace) obtain the full data

                        product = product_dict.get(product_data['sku'], None)
                        if not product:
                            url = cls._get_entry_url(product_element)
                            product = cls._assemble_full_product(
                                url, category, extra_args)
                    elif category == 'Headphones' and 'MPM' in \
                            product_data['sku']:
                        # Skip the thousands of headphones sold in marketplace
                        continue
                    else:
                        product = cls._assemble_product(
                            product_data, product_element, category)

                    if product:
                        if product.normal_price == Decimal('9999999') or \
                                product.offer_price == Decimal('9999999'):
                            continue

                        if product.sku in product_dict:
                            product_to_update = product_dict[product.sku]
                        else:
                            product_dict[product.sku] = product
                            product_to_update = product

                        product_to_update.positions[section_name] = position

                    position += 1

                pagination_tag = soup\
                    .find('div', 'catalog-page__footer-pagination')\
                    .find('ul', 'pagination')
                next_page_link_tag = pagination_tag.findAll('a')[-1]
                if next_page_link_tag['href'] == '#':
                    break

                if fast_mode and page >= 50:
                    break

                page += 1

        products_list = [p for p in product_dict.values()]

        return products_list

    @classmethod
    def _get_entry_url(cls, element):
        # Element Data (Varies by page)
        if element.name == 'div':
            url_extension = element.find('a')['href']
        else:
            url_extension = element['href']

        url = 'https://simple.ripley.cl{}'.format(url_extension)
        return url

    @classmethod
    def _assemble_full_product(cls, url, category, extra_args, retries=5):
        session = session_with_proxy(extra_args)
        if extra_args and 'user-agent' in extra_args:
            session.headers['user-agent'] = extra_args['user-agent']

        print(url)
        page_source = session.get(url, timeout=30).text

        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('div', 'error-page'):
            return []

        product_data = re.search(r'window.__PRELOADED_STATE__ = (.+);',
                                 page_source)
        if not product_data:
            if retries:
                return cls._assemble_full_product(url, category, extra_args,
                                                  retries=retries - 1)
            else:
                return None

        product_json = json.loads(product_data.groups()[0])

        if 'product' not in product_json:
            return None

        specs_json = product_json['product']['product']

        sku = specs_json['partNumber']
        name = specs_json['name'].encode('ascii', 'ignore').decode('ascii')
        short_description = specs_json.get('shortDescription', '')

        # If it's a cell sold by Ripley directly (not Mercado Ripley) add the
        # "Prepago" information in its description
        if category in ['Cell', 'Unknown'] and 'MPM' not in sku:
            name += ' ({})'.format(short_description)

        if specs_json['isOutOfStock'] or specs_json['isUnavailable']:
            stock = 0
        else:
            stock = -1

        if 'offerPrice' in specs_json['prices']:
            normal_price = Decimal(
                specs_json['prices']['offerPrice']).quantize(0)
        elif 'listPrice' in specs_json['prices']:
            normal_price = Decimal(
                specs_json['prices']['listPrice']).quantize(0)
        else:
            return []

        offer_price = Decimal(specs_json['prices'].get(
            'cardPrice', normal_price)).quantize(0)

        if offer_price > normal_price:
            offer_price = normal_price

        description = ''

        refurbished_notice = soup.find('div', 'emblemaReaccondicionados19')

        if refurbished_notice:
            description += html_to_markdown(str(refurbished_notice))

        if 'longDescription' in specs_json:
            description += html_to_markdown(specs_json['longDescription'])

        description += '\n\nAtributo | Valor\n-- | --\n'

        for attribute in specs_json['attributes']:
            if 'name' in attribute and 'value' in attribute:
                description += '{} | {}\n'.format(attribute['name'],
                                                  attribute['value'])

        description += '\n\n'
        condition = 'https://schema.org/NewCondition'

        if 'reacondicionado' in description.lower() or \
                'reacondicionado' in name.lower() or \
                'reacondicionado' in short_description.lower():
            condition = 'https://schema.org/RefurbishedCondition'

        if soup.find('img', {'src': '//home.ripley.cl/promo-badges/'
                                    'reacondicionado.png'}):
            condition = 'https://schema.org/RefurbishedCondition'

        picture_urls = []
        for path in specs_json['images']:
            picture_url = path

            if 'file://' in picture_url:
                continue

            if not picture_url.startswith('http'):
                picture_url = 'https:' + picture_url

            picture_urls.append(picture_url)

        if not picture_urls:
            picture_urls = None

        flixmedia_id = None
        video_urls = []

        flixmedia_urls = [
            '//media.flixfacts.com/js/loader.js',
            'https://media.flixfacts.com/js/loader.js'
        ]

        for flixmedia_url in flixmedia_urls:
            flixmedia_tag = soup.find(
                'script', {'src': flixmedia_url})
            if flixmedia_tag and flixmedia_tag.has_attr('data-flix-mpn'):
                flixmedia_id = flixmedia_tag['data-flix-mpn']
                video_urls = flixmedia_video_urls(flixmedia_id)
                break

        review_count = int(specs_json['powerReview']['fullReviews'])

        if review_count:
            review_avg_score = float(
                specs_json['powerReview']['averageRatingDecimal'])
        else:
            review_avg_score = None

        if 'shopName' in specs_json['marketplace']:
            seller = specs_json['marketplace']['shopName']
        elif specs_json['isMarketplaceProduct']:
            seller = 'Mercado R'
        else:
            seller = None

        print(url)

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
            flixmedia_id=flixmedia_id,
            review_count=review_count,
            review_avg_score=review_avg_score,
            video_urls=video_urls,
            seller=seller
        )

        return p

    @classmethod
    def _assemble_product(cls, data, element, category):
        # Element Data (Varies by page)
        if element.name == 'div':
            element_name = element.find(
                'a', 'ProductItem__Name').text.replace('  ', ' ').strip()
        else:
            element_name = element.find(
                'div', 'catalog-product-details__name') \
                .text.replace('  ', ' ').strip()

        # Common

        # This is removing extra white spaces in between words
        # If not done, sometimes it will not be equal to element name
        data_name = " ".join([a for a in data['name'].split(' ') if a != '']) \
            .strip()

        assert (element_name == data_name)

        # Remove weird characters, e.g.
        # https://simple.ripley.cl/tv-portatil-7-negro-mpm00003032468
        name = data_name.encode('ascii', 'ignore').decode('ascii')
        sku = data['sku']
        url = cls._get_entry_url(element)

        if 'image' in data:
            picture_url = 'https:{}'.format(data['image'])
            if validators.url(picture_url):
                picture_urls = [picture_url]
            else:
                picture_urls = None
        else:
            picture_urls = None

        if data['offers']['price'] == 'undefined':
            return None

        offer_price = Decimal(data['offers']['price']).quantize(0)
        normal_price_container = element.find(
            'li', 'catalog-prices__offer-price')

        if normal_price_container:
            normal_price = Decimal(
                element.find('li', 'catalog-prices__offer-price')
                .text.replace('$', '').replace('.', '')).quantize(0)
        else:
            normal_price = offer_price

        if normal_price < offer_price:
            offer_price = normal_price

        stock = 0
        if data['offers']['availability'] == 'http://schema.org/InStock':
            stock = -1

        if '-mpm' in url:
            seller = 'External seller'
        else:
            seller = None

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
            picture_urls=picture_urls,
            seller=seller
        )

        return p

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        if extra_args and 'user-agent' in extra_args:
            session.headers['user-agent'] = extra_args['user-agent']

        product_urls = []

        page = 1

        while True:
            if page > 40:
                raise Exception('Page overflow')

            search_url = 'https://simple.ripley.cl/api/v2/search'
            search_body = {
                "filters": [],
                "term": keyword,
                "perpage": 24,
                "page": page,
                "sessionkey": "",
                "sort": "score"
            }
            response = session.post(search_url, json=search_body)
            search_results = json.loads(response.text)

            if 'products' not in search_results:
                break

            for product in search_results['products']:
                product_urls.append(product['url'])
                if len(product_urls) >= threshold:
                    return product_urls

            page += 1

        return product_urls

    @classmethod
    def banners(cls, extra_args=None):
        extra_args = cls._extra_args_with_preflight(extra_args)
        base_url = 'https://simple.ripley.cl/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [bs.ELECTRO_RIPLEY, 'Electro Ripley',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'electro'],
            [bs.TECNO_RIPLEY, 'Tecno Ripley',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'tecno'],
            [bs.REFRIGERATION, 'Refrigeración',
             bs.SUBSECTION_TYPE_MOSAIC, 'electro/refrigeracion/'],
            [bs.REFRIGERATION, 'Side by Side',
             bs.SUBSECTION_TYPE_MOSAIC, 'electro/refrigeracion/side-by-side/'],
            [bs.REFRIGERATION, 'Refrigeradores', bs.SUBSECTION_TYPE_MOSAIC,
             'electro/refrigeracion/refrigeradores/'],
            [bs.REFRIGERATION, 'Freezers y congeladores',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/refrigeracion/freezers-y-congeladores/'],
            [bs.REFRIGERATION, 'Door In Door',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/refrigeracion/door-in-door/'],
            [bs.REFRIGERATION, 'Frigobar',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/refrigeracion/frigobar/'],
            [bs.REFRIGERATION, 'Refrigeracion Comercial e Industrial',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/refrigeracion/refrigeracion-comercial-e-industrial/'],
            [bs.WASHING_MACHINES, 'Lavandería',
             bs.SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia'],
            [bs.WASHING_MACHINES, 'Lavadoras',
             bs.SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia/lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadora-secadora',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/lavanderia/lavadora-secadora'],
            [bs.WASHING_MACHINES, 'Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/lavanderia/secadoras'],
            [bs.WASHING_MACHINES, 'Doble Carga',
             bs.SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia/doble-carga'],
            [bs.TELEVISIONS, 'Televisión',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/television'],
            [bs.TELEVISIONS, 'Smart TV',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/television/smart-tv'],
            [bs.TELEVISIONS, 'Ultra HD 4K',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/television/ultra-hd-4k'],
            [bs.TELEVISIONS, 'Premium y 8K',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecno/television/premium-tv-y-8k'],
            [bs.TELEVISIONS, 'HD y Full HD',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/television/hd-y-full-hd'],
            [bs.AUDIO, 'Audio y Música',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/audio-y-musica'],
            [bs.AUDIO, 'Parlantes Portables',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecno/audio-y-musica/parlantes-bluetooth'],
            [bs.AUDIO, 'Soundbar y Home theater',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecno/audio-y-musica/soundbar-y-home-theater'],
            [bs.AUDIO, 'Receiver y Amplificadores',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecno/audio-y-musica/receiver-y-amplificadores'],
            [bs.AUDIO, 'Equipos de música',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecno/audio-y-musica/equipos-de-musica'],
            [bs.AUDIO, 'Accesorios',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecno/audio-y-musica/accesorios-audio'],
            [bs.CELLS, 'Telefonía',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/celulares'],
            [bs.CELLS, 'iPhone',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/celulares/iphone']
        ]

        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                banners = banners + cls.get_owl_banners(
                    url, section, subsection, subsection_type, extra_args)

            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                banners = banners + cls.get_owl_banners(
                    url, section, subsection, subsection_type, extra_args)
            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                session = session_with_proxy(extra_args)

                if extra_args and 'user-agent' in extra_args:
                    session.headers['user-agent'] = extra_args['user-agent']

                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                if soup.find('svg', {'title': 'nofound'}):
                    logging.warning('Deactivated category: ' + url)
                    continue

                banners_container = soup.find('section', 'catalog-top-banner')

                if not banners_container:
                    print('No banners for: ' + url)
                    continue

                idx = 1
                for banner_link in banners_container.findAll('a'):
                    if 'item' in banner_link.attrs.get('class', []):
                        continue
                    picture_url = banner_link.find('img')

                    if not picture_url:
                        continue

                    banners.append({
                        'url': url,
                        'picture_url': picture_url.get('src') or
                        picture_url.get('data-src'),
                        'destination_urls': [banner_link['href']],
                        'key': picture_url.get('src') or
                        picture_url.get('data-src'),
                        'position': idx,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })
                    idx += 1
            else:
                raise Exception('Invalid subsection type')

        return banners

    @classmethod
    def get_owl_banners(cls, url, section, subsection, subsection_type,
                        extra_args):
        session = session_with_proxy(extra_args)

        if extra_args and 'user-agent' in extra_args:
            session.headers['user-agent'] = extra_args['user-agent']

        response = session.get(url + '?v=2')
        soup = BeautifulSoup(response.text, 'html.parser')
        carousel_tag = soup.find('div', 'home-carousel')
        banners = []

        if carousel_tag:
            carousel_tag = carousel_tag.find('div')
            for idx, banner_tag in enumerate(carousel_tag.findAll(
                    recursive=False)):
                if banner_tag.name == 'a':
                    destination_urls = [banner_tag['href']]
                    if banner_tag.find('img'):
                        picture_url = banner_tag.find('img')['src']
                    else:
                        picture_style = banner_tag.find('span')['style']
                        picture_url = re.search(r'url\((.+)\)',
                                                picture_style).groups()[0]

                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'destination_urls': destination_urls,
                        'key': picture_url,
                        'position': idx + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })
                else:
                    # Collage
                    desktop_container_tag = banner_tag.find('div')
                    cell_tags = desktop_container_tag.findAll('a')
                    destination_urls = [tag['href'] for tag in cell_tags
                                        if 'href' in tag.attrs]
                    picture_url = desktop_container_tag.find('source')[
                        'srcset']

                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'destination_urls': destination_urls,
                        'key': picture_url,
                        'position': idx + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })
        else:
            carousel_tag = soup.find('ul', 'splide__list')
            for idx, banner_tag in enumerate(carousel_tag.findAll('li')):
                banner_link = banner_tag.find('a')
                destination_urls = [banner_link['href']]
                picture_url = banner_link.find('img')['src']

                banners.append({
                    'url': url,
                    'picture_url': picture_url,
                    'destination_urls': destination_urls,
                    'key': picture_url,
                    'position': idx + 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type
                })

        return banners

    @classmethod
    def reviews_for_sku(cls, sku):
        print(sku)
        session = session_with_proxy(None)
        reviews = []
        page = 1

        while True:
            print(page)
            reviews_endpoint = 'https://display.powerreviews.com/m/303286/l/' \
                               'es_ES/product/{}/reviews?' \
                               'apikey=71f6caaa-ea4f-43b9-a19e-46eccb73bcbb' \
                               '&paging.size=25&paging.from={}'.format(
                                    sku, page)
            response = session.get(reviews_endpoint).json()

            if response['paging']['current_page_number'] != page:
                break

            for entry in response['results'][0]['reviews']:
                review_date = datetime.fromtimestamp(
                    entry['details']['created_date'] / 1000)

                review = {
                    'store': 'Ripley',
                    'sku': sku,
                    'rating': float(entry['metrics']['rating']),
                    'text': entry['details']['comments'],
                    'date': review_date.isoformat()
                }

                reviews.append(review)

            page += 1

        return reviews
