import json
import logging
import random
import re
import time

from collections import defaultdict
from decimal import Decimal
from bs4 import BeautifulSoup
from html import unescape

from dateutil.parser import parse

from storescraper.categories import GAMING_CHAIR, STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy, \
    CF_REQUEST_HEADERS
from storescraper import banner_sections as bs


class Falabella(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 20

    category_paths = [
        ['cat70057', ['Notebook'],
         'Home > Computación-Notebooks', 1],
        ['cat5860031', ['Notebook'],
         'Home > Computación-Notebooks > Notebooks Tradicionales', 1],
        ['cat2028', ['Notebook'],
         'Home > Computación-Notebooks Gamers', 1],
        ['cat2450060', ['Notebook'],
         'Home > Computación-Notebooks > Notebooks Convertibles 2en1', 1],
        ['cat15880017', ['Notebook'],
         'Home > Especiales-Gamer', 1],
        ['cat5860030', ['Notebook'],
         'Home > Computación-Notebooks > MacBooks', 1],
        ['cat4850013', ['Notebook'],
         'Home > Computación-Computación Gamer', 1],
        ['cat1012', ['Television'],
         'Home > Tecnología-TV', 1],
        ['cat7190148', ['Television'],
         'Home > Tecnología-TV > Televisores LED', 1],
        ['cat11161614', ['Television'],
         'Home > Tecnología-TV > LEDs menores a 50 pulgadas', 1],
        ['cat11161675', ['Television'],
         'Home > Tecnología-TV > LEDs entre 50 - 55 pulgadas', 1],
        ['cat11161679', ['Television'],
         'Home > Tecnología-TV > LEDs sobre 55 pulgadas', 1],
        ['cat2850016', ['Television'],
         'Home > TV-Televisores OLED', 1],
        ['cat10020021', ['Television'],
         'Home > TV-Televisores QLED', 1],
        ['cat18110001', ['Television'],
         'Home > Tecnología-Premium', 1],
        ['cat7230007', ['Tablet'],
         'Home > Computación-Tablets', 1],
        ['cat3205', ['Refrigerator'],
         'Home > Electrohogar-Línea Blanca > Refrigeradores', 1],
        ['cat4048', ['Refrigerator'],
         'Home > Electrohogar-Línea Blanca > Refrigeradores > Freezers', 1],
        ['cat4049', ['Refrigerator'],
         'Home > Electrohogar-Línea Blanca > Refrigeradores > Frigobar', 1],
        ['cat4091', ['Refrigerator'],
         'Home > Refrigeración-Side by Side', 1],
        ['cat1820006', ['Printer'],
         'Home > Computación-Impresión > Impresoras Multifuncionales', 1],
        ['cat2049', ['Printer'],
         'Home > Tecnología-Computadores > Impresoras', 1],
        ['cat3151', ['Oven'],
         'Home > Microondas', 1],
        ['cat3114', ['Oven'],
         'Home > Electrodomésticos Cocina- Electrodomésticos de cocina > '
         'Hornos Eléctricos', 1],
        ['cat3025', ['VacuumCleaner'],
         'Home > Electrohogar- Aspirado y Limpieza > Aspiradoras', 1],
        ['cat3136', ['WashingMachine'],
         'Home > Electrohogar-Lavado > Lavado', 1],
        ['cat4060', ['WashingMachine'],
         'Home > Electrohogar-Lavado > Lavadoras', 1],
        ['cat1700002', ['WashingMachine'],
         'Home > Electrohogar-Lavado > Lavadoras-Secadoras', 1],
        ['cat4088', ['WashingMachine'],
         'Home > Electrohogar-Lavado > Secadoras', 1],
        ['cat1280018', ['Cell'],
         'Home > Telefonía- Celulares y Teléfonos > Celulares Básicos', 1],
        ['cat720161', ['Cell'],
         'Home > Telefonía- Celulares y Teléfonos > Smartphones', 1],
        ['cat70028', ['Camera'],
         'Home > Fotografía-Cámaras Compactas', 1],
        ['cat70029', ['Camera'],
         'Home > Fotografía-Cámaras Semiprofesionales', 1],
        ['cat2005', ['StereoSystem'],
         'Home > Tecnología-Audio', 0],
        ['cat3091', ['StereoSystem'],
         'Home > Tecnología-Audio > Equipos de Música y Karaokes', 1],
        ['cat3171', ['StereoSystem'],
         'Home > Tecnología-Audio > Parlantes Bluetooth', 1],
        ['cat2045', ['StereoSystem'],
         'Home > Tecnología-Audio > Soundbar y Home Theater', 1],
        ['cat1130010', ['StereoSystem'],
         'Home > Audio- Hi-Fi > Tornamesas', 1],
        ['cat6260041', ['StereoSystem'],
         'Home > Día del Niño Chile- Tecnología > Audio > Karaoke', 1],
        ['cat2032', ['OpticalDiskPlayer'],
         'Home > TV-Blu Ray y DVD', 1],
        ['cat3087', ['ExternalStorageDrive'],
         'Home > Computación- Almacenamiento > Discos duros', 1],
        ['cat3177', ['UsbFlashDrive'],
         'Home > Computación- Almacenamiento > Pendrives', 1],
        ['cat70037', ['MemoryCard'],
         'Home > Computación- Accesorios Tecnología > '
         'Accesorios Fotografía > Tarjetas de Memoria', 1],
        ['cat2070', ['Projector'],
         'Home > TV-Proyectores', 1],
        ['cat3770004', ['VideoGameConsole'],
         'Home > Tecnología- Videojuegos > Consolas', 1],
        ['cat4440005', ['VideoGameConsole'],
         'Home > Tecnología-Videojuegos > Playstation', 1],
        ['cat70003', ['VideoGameConsole'],
         'Home > Tecnología-Videojuegos > Nintendo', 1],
        ['cat4440004', ['VideoGameConsole'],
         'Home > Tecnología-Videojuegos > Xbox', 1],
        ['cat40051', ['AllInOne'],
         'Home > Computación-All In One', 1],
        ['cat7830015', ['AirConditioner'],
         'Home > Electrohogar- Aire Acondicionado > Portátiles', 1],
        ['cat7830014', ['AirConditioner'],
         'Home > Electrohogar- Aire Acondicionado >Split', 1],
        ['cat3197', ['AirConditioner'],
         'Home > Electrohogar- Aire Acondicionado > Purificadores', 1],
        ['cat2062', ['Monitor'],
         'Home > Computación-Monitores', 1],
        ['cat2013', ['WaterHeater'],
         'Home > Electrohogar- Aire Acondicionado > Calefont y Termos', 1],
        ['cat3155', ['Mouse'],
         'Home > Computación- Accesorios Tecnología > '
         'Accesorios Computación > Mouse', 1],
        ['cat9900007', ['SpaceHeater'],
         'Home > Electrohogar- Calefacción > Estufas Parafina Láser', 1],
        ['cat9910024', ['SpaceHeater'],
         'Home > Electrohogar- Calefacción > Estufas Gas', 1],
        ['cat9910006', ['SpaceHeater'],
         'Home > Electrohogar- Calefacción > Estufas Eléctricas', 1],
        ['cat9910027', ['SpaceHeater'],
         'Home > Electrohogar- Calefacción > Estufas Pellet y Leña', 1],
        ['cat4290063', ['Wearable'],
         'Home > Telefonía- Wearables > SmartWatch', 1],
        ['cat4730023', ['Keyboard'],
         'Home > Computación- Accesorios Tecnología > '
         'Accesorios Computación > Teclados > Teclados Gamers', 1],
        ['cat2370002', ['Keyboard'],
         'Home > Computación- Accesorios Tecnología > '
         'Accesorios Computación > Teclados', 1],
        ['cat2930003', ['Keyboard'],
         'Home > Computación- Accesorios Tecnología > Accesorios TV > '
         'Teclados Smart', 1],
        ['cat1640002', ['Headphones'],
         'Home > Tecnología-Audio > Audífonos', 1],
        ['cat3239', [STEREO_SYSTEM],
         'Home > Tecnología-Audio > Parlantes y Subwoofer', 1],
        ['cat3203', [STEREO_SYSTEM],
         'Home > Tecnología-Audio > Hi-Fi', 1],
        ['cat4061', ['DishWasher'],
         'Home > Lavado-Lavavajillas', 1],
        ['cat12084890', [GAMING_CHAIR],
         'Home > Tecnología-Computadores > Accesorios Computación > Sillas '
         'Gamer', 1]
    ]

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
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Projector',
            'VideoGameConsole',
            'CellAccesory',
            'AllInOne',
            'AirConditioner',
            'Monitor',
            'WaterHeater',
            'SolidStateDrive',
            'Mouse',
            'SpaceHeater',
            'Keyboard',
            'KeyboardMouseCombo',
            'Wearable',
            'Headphones',
            'DishWasher',
            GAMING_CHAIR
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = cls.category_paths
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = CF_REQUEST_HEADERS['User-Agent']
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = \
                e[:4]

            if len(e) > 4:
                extra_query_params = e[4]
            else:
                extra_query_params = None

            if category not in local_categories:
                continue

            category_product_urls = cls._get_product_urls(
                session, category_id, extra_query_params)

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
        session.headers['User-Agent'] = CF_REQUEST_HEADERS['User-Agent']

        base_url = "https://www.falabella.com/falabella-cl/search?" \
                   "Ntt={}&page={}"

        discovered_urls = []
        page = 1
        while True:
            if page > 150:
                raise Exception('Page overflow ' + keyword)

            search_url = base_url.format(keyword, page)
            res = session.get(search_url, timeout=30)

            if res.status_code == 500:
                break

            soup = BeautifulSoup(res.text, 'html.parser')

            script = soup.find('script', {'id': '__NEXT_DATA__'})
            json_data = json.loads(script.text)

            if 'results' not in json_data['props']['pageProps']:
                break

            for product_data in json_data['props']['pageProps']['results']:
                product_url = product_data['url']
                discovered_urls.append(product_url)

                if len(discovered_urls) == threshold:
                    return discovered_urls

            page += 1

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = CF_REQUEST_HEADERS['User-Agent']

        for i in range(3):
            response = session.get(url, timeout=30)

            if response.status_code in [404, 500]:
                return []

            content = response.text.replace('&#10;', '')

            if 'fbra_browseMainProductConfig' in content:
                print('NEW')
                return cls._new_products_for_url(
                    url, content, session,
                    category=category, extra_args=extra_args)
            elif 'NEXT_DATA' in content:
                print('OLD')
                return cls._old_products_for_url(
                    url, content, session,
                    category=category, extra_args=extra_args)
            else:
                raise Exception('Invalid product type')

    @classmethod
    def _get_product_urls(cls, session, category_id, extra_query_params):
        discovered_urls = []
        base_url = 'https://www.falabella.com/s/browse/v1/listing/cl?' \
                   'zones=ZL_CERRILLOS%2CLOSC%2C130617%2C13' \
                   '&categoryId={}&page={}'

        page = 1

        while True:
            if page > 200:
                raise Exception('Page overflow: ' + category_id)

            pag_url = base_url.format(category_id, page)
            print(pag_url)

            if extra_query_params:
                pag_url += '&' + extra_query_params

            res = cls.retrieve_json_page(session, pag_url)

            if 'results' not in res or not res['results']:
                if page == 1:
                    logging.warning('Empty category: {}'.format(category_id))
                break

            for result in res['results']:
                product_url = result['url']

                discovered_urls.append(product_url)

            page += 1

        return discovered_urls

    @classmethod
    def retrieve_json_page(cls, session, url, retries=5):
        if '?' in url:
            separator = '&'
        else:
            separator = '?'

        modified_url = '{}{}v={}'.format(url, separator, random.random())

        try:
            res = session.get(modified_url, timeout=30)
            return json.loads(res.content.decode('utf-8'))['data']
        except Exception:
            if retries > 0:
                time.sleep(3)
                return cls.retrieve_json_page(session, url, retries=retries-1)
            else:
                raise

    @classmethod
    def _new_products_for_url(
            cls, url, content, session, category=None, extra_args=None):
        product_data = json.loads(re.search(
            r'var fbra_browseMainProductConfig = ([\S\s]+?);\r\n',
            content).groups()[0])['state']['product']

        publication_id = product_data['id']
        brand = product_data['brand'] or 'Genérico'
        base_name = '{} {}'.format(brand, product_data['displayName'])
        slug = product_data['displayName'].replace(' ', '-')

        seller = None
        if product_data['isMarketPlace']:
            seller = product_data['fulFilledBy']

        products = []

        for model in product_data['skus']:
            sku = model['skuId']
            sku_url = 'https://www.falabella.com/falabella-cl/product/{}/{}/' \
                      '{}'.format(publication_id, slug, sku)
            prices = {e['type']: e for e in model['price']}
            normal_price_keys = [3]
            offer_price_keys = [1]

            if not prices:
                continue

            normal_price = None
            offer_price = None

            for key in normal_price_keys:
                if key not in prices:
                    continue
                normal_price = Decimal(
                    remove_words(prices[key]['originalPrice']))
                break

            for key in offer_price_keys:
                if key not in prices:
                    continue
                offer_price = Decimal(
                    remove_words(prices[key]['originalPrice']))

            if not offer_price:
                offer_price = normal_price

            if not normal_price:
                normal_price = offer_price

            stock = model['stockAvailable']
            picture_urls = cls._get_picture_urls(session, model['skuId'])

            # TODO: Video Urls

            # REVIEWS
            reviews_url = 'https://api.bazaarvoice.com/data/reviews.json?' \
                          'apiversion=5.4&passkey=mk9fosfh4vxv20y8u5pcbwipl&' \
                          'Filter=ProductId:{}&Include=Products&Stats=' \
                          'Reviews'.format(sku)

            review_data = json.loads(session.get(reviews_url, timeout=30).text)
            review_count = review_data['TotalResults']

            review_stats = review_data['Includes']

            if 'Products' in review_stats:
                if str(sku) not in review_stats['Products'].keys():
                    key = list(review_stats['Products'].keys())[0]
                    review_avg_score = review_stats['Products'][key][
                        'ReviewStatistics']['AverageOverallRating']
                else:
                    review_avg_score = review_stats['Products'][str(sku)][
                        'ReviewStatistics']['AverageOverallRating']
            else:
                review_avg_score = None

            # CONDITION
            if 'reacondicionado' in base_name.lower():
                condition = 'https://schema.org/RefurbishedCondition'
            else:
                condition = 'https://schema.org/NewCondition'

            p = Product(
                base_name[:200],
                cls.__name__,
                category,
                sku_url,
                url,
                sku,
                stock,
                normal_price,
                offer_price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,
                review_count=review_count,
                review_avg_score=review_avg_score,
                condition=condition,
                seller=seller
            )

            products.append(p)

        return products

    @classmethod
    def _old_products_for_url(
            cls, url, content, session, category=None, extra_args=None):
        soup = BeautifulSoup(content, 'html.parser')
        next_container = soup.find('script', {'id': '__NEXT_DATA__'})

        if not next_container:
            return []

        product_data = json.loads(
            next_container.text)[
            'props']['pageProps']['productData']

        specification = soup.find('div', 'productInfoContainer')
        long_description = product_data['longDescription']

        if long_description:
            description_soup = BeautifulSoup(
                unescape(long_description), 'html.parser')
        else:
            description_soup = None

        panels = [specification, description_soup]
        video_urls = []

        for panel in panels:
            if not panel:
                continue

            for iframe in panel.findAll('iframe'):
                match = re.search(
                    r'//www.youtube.com/embed/(.+)\?', iframe['src'])
                if not match:
                    match = re.search(
                        r'//www.youtube.com/embed/(.+)', iframe['src'])
                if match:
                    video_urls.append('https://www.youtube.com/watch?v={}'
                                      .format(match.groups()[0].strip()))

        slug = product_data['slug']
        publication_id = product_data['id']
        brand = product_data['brandName'] or 'Genérico'
        base_name = '{} {}'.format(brand, product_data['name'])

        products = []

        if 'variants' not in product_data:
            return []

        for model in product_data['variants']:
            sku = model['id']
            sku_url = 'https://www.falabella.com/falabella-cl/product/{}/{}/' \
                      '{}'.format(publication_id, slug, sku)

            prices = {e['type']: e for e in model['prices']}

            if not prices:
                continue

            normal_price_keys = ['internetPrice', 'normalPrice']
            offer_price_keys = ['cmrPrice', 'eventPrice']

            normal_price = None
            offer_price = None

            for key in normal_price_keys:
                if key not in prices:
                    continue
                normal_price = Decimal(remove_words(prices[key]['price'][0]))
                if normal_price.is_finite():
                    break
                else:
                    normal_price = None

            for key in offer_price_keys:
                if key not in prices:
                    continue
                offer_price = Decimal(remove_words(prices[key]['price'][0]))
                if offer_price.is_finite():
                    break
                else:
                    offer_price = None

            if not normal_price and not offer_price:
                # No valid prices found
                continue

            if not offer_price:
                offer_price = normal_price

            if not normal_price:
                normal_price = offer_price

            stock = 0

            if model.get('isPurchaseable', False):
                availabilities = model['availability']

                for availability in availabilities:
                    if availability['shippingOptionType'] in \
                            ['All', 'HomeDelivery', 'SiteToStore',
                             'PickupInStore']:
                        stock = availability['quantity']

            reviews_url = 'https://api.bazaarvoice.com/data/reviews.json?' \
                          'apiversion=5.4&passkey=mk9fosfh4vxv20y8u5pcbwipl&' \
                          'Filter=ProductId:{}&Include=Products&Stats=' \
                          'Reviews'.format(sku)

            review_data = json.loads(session.get(reviews_url, timeout=30).text)
            review_count = review_data['TotalResults']

            review_stats = review_data['Includes']

            if 'Products' in review_stats:
                if str(sku) not in review_stats['Products'].keys():
                    key = list(review_stats['Products'].keys())[0]
                    review_avg_score = review_stats['Products'][key][
                        'ReviewStatistics']['AverageOverallRating']
                else:
                    review_avg_score = review_stats['Products'][str(sku)][
                        'ReviewStatistics']['AverageOverallRating']
            else:
                review_avg_score = None

            if 'reacondicionado' in base_name.lower():
                condition = 'https://schema.org/RefurbishedCondition'
            else:
                condition = 'https://schema.org/NewCondition'

            seller = None
            if model['offerings'] and 'falabella' not in \
                    model['offerings'][0]['sellerId'].lower():
                seller = model['offerings'][0]['sellerId']

            picture_urls = cls._get_picture_urls(session, model['id'])

            p = Product(
                '{} ({})'.format(base_name, model['name'])[:200],
                cls.__name__,
                category,
                sku_url,
                url,
                sku,
                stock,
                normal_price,
                offer_price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,
                video_urls=video_urls,
                review_count=review_count,
                review_avg_score=review_avg_score,
                condition=condition,
                seller=seller
            )

            products.append(p)

        return products

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.falabella.com/falabella-cl/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],

            # # CATEGORY PAGES # #
            [bs.REFRIGERATION, 'Electrohogar-Refrigeradores',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat3205/Refrigeradores?isLanding=true'],
            # [bs.WASHING_MACHINES, 'Electrohogar-Lavado',
            #  bs.SUBSECTION_TYPE_CATEGORY_PAGE,
            #  'category/cat3136/Lavado?isLanding=true'],
            # [bs.TELEVISIONS, 'TV', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
            #  'category/cat1012/TV?isLanding=true'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat2005/Audio?isLanding=true'],
            [bs.CELLS, 'Telefonía-Celulares y Teléfonos',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat2018/Celulares-y-Telefonos?isLanding=true'],

            # # MOSAICS ##
            [bs.LINEA_BLANCA_FALABELLA, 'Electro y Tecnología-Línea Blanca',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat7090035/Linea-Blanca?isPLP=1'],
            [bs.REFRIGERATION, 'Refrigeradores-No Frost',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4074/No-Frost'],
            [bs.REFRIGERATION, 'Refrigeradores-Side by Side',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4091/Side-by-Side'],
            [bs.WASHING_MACHINES, 'Lavadoras', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3136/Lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Lavadoras',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4060/Lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1700002/Lavadoras-Secadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4088/Secadoras'],
            [bs.WASHING_MACHINES, ' Lavadoras-Lavadoras Doble Carga',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat11400002/Lavadoras-Doble-Carga'],
            [bs.TELEVISIONS, 'Tecnología-TV', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1012/TV?isPLP=1'],
            [bs.TELEVISIONS, 'Televisores LED', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat7190148/Televisores-LED'],
            [bs.TELEVISIONS, 'LEDs menores a 50 pulgadas',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat11161614/LEDs-menores-a-50-pulgadas'],
            [bs.TELEVISIONS, 'LEDs entre 50 - 55 pulgadas',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat11161675/LEDs-entre-50---55-pulgadas'],
            [bs.TELEVISIONS, 'LEDs sobre 55 pulgadas',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat11161679/LEDs-sobre-55-pulgadas'],
            [bs.TELEVISIONS, 'TV-LED', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat2850014/LED'],
            [bs.TELEVISIONS, 'TV-Smart TV', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3040054/Smart-TV'],
            [bs.TELEVISIONS, 'TV-4K UHD', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3990038/4K-UHD'],
            [bs.TELEVISIONS, 'TV-Televisores OLED', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat2850016/Televisores-OLED'],
            [bs.TELEVISIONS, 'TV-Pulgadas Altas',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat12910024/Televisores-LED-Desde-65"'],
            [bs.AUDIO, 'Audio-Soundbar y Home Theater',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat2045/Home-Theater'],
            [bs.AUDIO, 'Home Theater', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3050040/Home-Theater'],
            [bs.AUDIO, 'Soundbar', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1700004/Soundbar'],
            [bs.AUDIO, 'Minicomponente', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat70018/Minicomponente'],
            [bs.AUDIO, 'Audio-Equipos de Música y Karaokes',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3091/?mkid=CA_P2_MIO1_024794'],
            [bs.AUDIO, 'Audio-Hi-Fi', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3203/Hi-Fi'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat2005/Audio?isPLP=1'],
            [bs.CELLS, 'Smartphones', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat720161/Smartphones'],
            [bs.CELLS, 'Electro y Tecnología-Teléfonos',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat2018/Telefonos?isPLP=1'],
        ]

        banners = []
        proxy = extra_args['proxy']

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                session = session_with_proxy(extra_args)
                session.headers['User-Agent'] = CF_REQUEST_HEADERS[
                    'User-Agent']
                soup = BeautifulSoup(session.get(url, timeout=30).text,
                                     'html.parser')
                next_data = json.loads(soup.find(
                    'script', {'id': '__NEXT_DATA__'}).text)

                for container in \
                        next_data['props']['pageProps']['page']['containers']:
                    if container['key'] == 'showcase':
                        showcase_container = container
                        break
                else:
                    raise Exception('No showcase container found')

                slides = showcase_container['components'][0]['data']['slides']

                for idx, slide in enumerate(slides):
                    main_url = slide.get('mainUrl', None)
                    if main_url:
                        destination_urls = [main_url]
                    elif slide['type'] == 'background_image_only':
                        destination_urls = []
                    else:
                        destination_urls = list(
                            {slide['urlLeft'], slide['urlRight']})
                    picture_url = slide['imgBackgroundDesktopUrl']

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
            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                session = session_with_proxy(extra_args)
                session.headers['User-Agent'] = CF_REQUEST_HEADERS[
                    'User-Agent']
                soup = BeautifulSoup(session.get(url, timeout=30).text,
                                     'html.parser')
                next_data = json.loads(soup.find(
                    'script', {'id': '__NEXT_DATA__'}).text)

                for container in \
                        next_data['props']['pageProps']['page']['containers']:
                    if container['key'] == 'main-right':
                        showcase_container = container
                        break
                else:
                    raise Exception('No showcase container found')

                slides = showcase_container['components'][0]['data']['slides']

                for idx, slide in enumerate(slides):
                    main_url = slide.get('mainUrl', None)
                    if main_url:
                        destination_urls = [main_url]
                    elif slide['type'] == 'background_image_only':
                        destination_urls = []
                    else:
                        destination_urls = list(
                            {slide['urlLeft'], slide['urlRight']})
                    picture_url = slide['imgBackgroundDesktopUrl']

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
            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                session = session_with_proxy(extra_args)
                session.headers['User-Agent'] = CF_REQUEST_HEADERS[
                    'User-Agent']
                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                banner = soup.find('div', 'fb-huincha-main-wrap')

                if not banner:
                    print('No banner for ' + url)
                    continue

                image_url = banner.find('source')['srcset']
                dest_url = banner.find('a')['href']

                banners.append({
                    'url': url,
                    'picture_url': image_url,
                    'destination_urls': [dest_url],
                    'key': image_url,
                    'position': 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type})

        return banners

    @classmethod
    def _get_picture_urls(cls, session, product_id):
        pictures_resource_url = 'https://falabella.scene7.com/is/image/' \
                                'Falabella/{}?req=set,json'.format(product_id)
        pictures_response = session.get(pictures_resource_url, timeout=30).text
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      pictures_response).groups()[0])

        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https://falabella.scene7.com/is/image/{}?' \
                          'wid=1500&hei=1500&qlt=70'.format(
                            picture_entry['i']['n'])
            picture_urls.append(picture_url)

        return picture_urls

    @classmethod
    def reviews_for_sku(cls, sku):
        print(sku)
        session = session_with_proxy(None)
        reviews = []
        offset = 0

        while True:
            print(offset)
            endpoint = 'https://api.bazaarvoice.com/data/batch.json?' \
                       'passkey=m8bzx1s49996pkz12xvk6gh2e&apiversion=' \
                       '5.5&resource.q0=reviews&filter.q0=isratings' \
                       'only%3Aeq%3Afalse&filter.q0=productid%3Aeq' \
                       '%3A{}&limit.q0=100&offset.q0={}'.format(sku, offset)
            response = session.get(endpoint).json()[
                'BatchedResults']['q0']['Results']

            if not response:
                break

            for entry in response:
                review_date = parse(entry['SubmissionTime'])

                review = {
                    'store': 'Falabella',
                    'sku': sku,
                    'rating': float(entry['Rating']),
                    'text': entry['ReviewText'],
                    'date': review_date.isoformat()
                }

                reviews.append(review)

            offset += 100

        return reviews
