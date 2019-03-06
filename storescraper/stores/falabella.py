import json
import urllib
from collections import OrderedDict
from decimal import Decimal

import re

import time
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy
from storescraper import banner_sections as bs
from storescraper.utils import HeadlessChrome


class Falabella(Store):
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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_paths = [
            ['cat5860031/Notebooks-Convencionales', 'Notebook'],
            ['cat2028/Notebooks-Gamers', 'Notebook'],
            ['cat2450060/Notebooks-2-en-1', 'Notebook'],
            ['cat5860030/MacBooks', 'Notebook'],
            ['cat4850013/Computacion-Gamer', 'Notebook'],
            # ['cat7190196/Ver-tod-Computadores', 'Notebook'],
            ['cat7190148/Televisores-LED', 'Television'],
            ['cat7230007/Tablet', 'Tablet'],
            ['cat4074/No-Frost', 'Refrigerator'],
            ['cat4091/Side-by-Side', 'Refrigerator'],
            ['cat4036/Frio-Directo', 'Refrigerator'],
            ['cat4048/Freezer', 'Refrigerator'],
            ['cat4049/Frigobar', 'Refrigerator'],
            ['cat1840004/Cavas-de-Vino', 'Refrigerator'],
            ['cat1820006/Impresoras-Multifuncionales', 'Printer'],
            # ['cat11970007/Impresoras-Laser', 'Printer'],
            ['cat6680042/Impresoras-Tradicionales', 'Printer'],
            # ['cat11970009/Impresoras-Fotograficas', 'Printer'],
            ['cat3151/Microondas', 'Oven'],
            ['cat3114/Hornos-Electricos', 'Oven'],
            ['cat3025/Aspiradoras-y-Enceradoras', 'VacuumCleaner'],
            ['cat4060/Lavadoras', 'WashingMachine'],
            ['cat1700002/Lavadora-Secadora', 'WashingMachine'],
            ['cat4088/Secadoras', 'WashingMachine'],
            ['cat1280018/Celulares-Basicos', 'Cell'],
            ['cat720161/Smartphones', 'Cell'],
            ['cat70028/Camaras-Compactas', 'Camera'],
            ['cat70029/Camaras-Semiprofesionales', 'Camera'],
            ['cat3091/Equipos-de-Musica', 'StereoSystem'],
            ['cat3171/Parlantes-Bluetooth', 'StereoSystem'],
            ['cat2045/Soundbar y Home Theater', 'StereoSystem'],
            ['cat1130010/Tornamesas', 'StereoSystem'],
            ['cat6260041/Karaoke', 'StereoSystem'],
            ['cat2032/DVD-y-Blu-Ray', 'OpticalDiskPlayer'],
            ['cat3087/Discos-duros', 'ExternalStorageDrive'],
            ['cat3177/Pendrives', 'UsbFlashDrive'],
            ['cat70037/Tarjetas-de-Memoria', 'MemoryCard'],
            ['cat2070/Proyectores', 'Projector'],
            ['cat3770004/Consolas', 'VideoGameConsole'],
            ['cat40051/All-In-One', 'AllInOne'],
            ['cat7830015/Portatiles', 'AirConditioner'],
            ['cat7830014/Split', 'AirConditioner'],
            # ['cat2062/Monitores', 'Monitor'],
            ['cat2013/Calefont-y-Termos', 'WaterHeater'],
            ['cat3155/Mouse', 'Mouse'],
            ['cat9900007/Estufas-Parafina', 'SpaceHeater'],
            ['cat9910024/Estufas-Gas', 'SpaceHeater'],
            ['cat9910006/Estufas-Electricas', 'SpaceHeater'],
            ['cat9910027/Estufas-Pellet-y-Lena', 'SpaceHeater'],
            ['cat4290063/SmartWatch', 'Wearable'],
            ['cat4730023/Teclados-Gamers', 'Keyboard'],
            ['cat2370002/Teclados', 'Keyboard'],
            ['cat2930003/Teclados-Smart', 'Keyboard'],
            ['cat1640002/Audifonos', 'Headphones'],
        ]

        session = session_with_proxy(extra_args)
        session.headers.update({
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en,en-US;q=0.8,es;q=0.6',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'DNT': '1',
            'Host': 'www.falabella.com',
            'Referer': 'https://www.falabella.com/falabella-cl/',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 '
                          'Safari/537.36'
        })
        session.get('https://www.falabella.com/falabella-cl/', timeout=30)
        session.get('https://www.falabella.com/falabella-cl/'
                    'includes/ajaxFirstNameAndCartQuantity.jsp', timeout=30)
        discovered_urls = []

        for url_path, local_category in url_paths:
            if local_category != category:
                continue

            print(url_path)

            sorters = [
                None,  # No sorting
                1,  # Precio menor a mayor
                2,  # Precio mayor a menor
                3,  # Marca
                4,  # Destacados
                5,  # Recomendados
                6,  # Mejor evaluados
                7,  # Nuevos productos
            ]

            # Falabella tends to... fail... so try different requests using
            # the different available sorters... twice... just in case.
            category_product_urls = []

            for i in range(2 * len(sorters)):
                try:
                    category_product_urls = cls._get_category_product_urls(
                        session,
                        url_path,
                        sorters[i % len(sorters)]
                    )
                    break
                except Exception:
                    continue

            if not category_product_urls:
                raise Exception('Category error: ' + url_path)

            discovered_urls.extend(category_product_urls)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        return cls._products_for_url(url, category=category,
                                     extra_args=extra_args)

    @classmethod
    def _get_category_product_urls(cls, session, url_path, sorter):
        discovered_urls = []
        query_args = OrderedDict([
            ('currentPage', 1),
            # ('sortBy', sorter),
            ('navState', "/category/{}?sortBy={}".format(url_path, sorter))])

        if not sorter:
            query_args['navState'] = "/category/{}".format(url_path)

        page = 1

        while True:
            print(page)
            if page > 60:
                raise Exception('Page overflow: ' + url_path)

            res = None

            error_count = 0
            while res is None or 'errors' in res:
                error_count += 1
                if error_count > 10:
                    raise Exception('Error threshold exceeded: ' + url_path)
                query_args['currentPage'] = page
                pag_url = 'https://www.falabella.com/rest/model/' \
                          'falabella/rest/browse/BrowseActor/' \
                          'get-product-record-list?{}'.format(
                            urllib.parse.quote(json.dumps(
                                query_args, separators=(',', ':')), safe=''))

                res = json.loads(
                    session.get(pag_url, timeout=30).content.decode('utf-8'))

            if not res['state']['resultList'] and page == 1:
                raise Exception('Empty category path: ' + url_path)

            for product_entry in res['state']['resultList']:
                product_id = product_entry['productId'].strip()
                product_url = \
                    'https://www.falabella.com/falabella-cl/product/{}/' \
                    ''.format(product_id)
                discovered_urls.append(product_url)

            if res['state']['pagesTotal'] == page:
                break

            page += 1

        return discovered_urls

    @classmethod
    def _products_for_url(cls, url, retries=5, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        content = session.get(url, timeout=30).text.replace('&#10;', '')

        soup = BeautifulSoup(content, 'html.parser')

        panels = ['fb-product-information__product-information-tab',
                  'fb-product-information__specification']

        description = ''

        for panel in panels:
            description += html_to_markdown(str(soup.find('div', panel))) + \
                           '\n\n'

        raw_json_data = re.search('var fbra_browseMainProductConfig = (.+);\r',
                                  content)

        if not raw_json_data:
            if retries:
                time.sleep(5)
                return cls._products_for_url(
                    url, retries=retries-1, category=category,
                    extra_args=extra_args)
            else:
                return []

        product_data = json.loads(raw_json_data.groups()[0])

        brand = product_data['state']['product']['brand']
        model = product_data['state']['product']['displayName']
        full_name = '{} {}'.format(brand, model)

        global_id = product_data['state']['product']['id']
        media_asset_url = product_data['endPoints']['mediaAssetUrl']['path']

        pictures_resource_url = 'https://falabella.scene7.com/is/image/' \
                                'Falabella/{}?req=set,json'.format(global_id)
        pictures_response = session.get(pictures_resource_url, timeout=30).text
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      pictures_response).groups()[0])

        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https:{}{}?scl=1.0'.format(media_asset_url,
                                                      picture_entry['i']['n'])
            picture_urls.append(picture_url)

        products = []
        for model in product_data['state']['product']['skus']:
            if 'stockAvailable' not in model:
                continue

            sku = model['skuId']

            prices = {e['type']: e for e in model['price']}

            if 3 in prices:
                normal_price_key = 3
            else:
                normal_price_key = 2

            lookup_field = 'originalPrice'
            if lookup_field not in prices[normal_price_key]:
                lookup_field = 'formattedLowestPrice'

            normal_price = Decimal(remove_words(
                prices[normal_price_key][lookup_field]))

            if 1 in prices:
                lookup_field = 'originalPrice'
                if lookup_field not in prices[1]:
                    lookup_field = 'formattedLowestPrice'
                offer_price = Decimal(
                    remove_words(prices[1][lookup_field]))
            else:
                offer_price = normal_price

            stock = model['stockAvailable']

            p = Product(
                full_name,
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

            products.append(p)

        return products

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.falabella.com/falabella-cl/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            # [LINEA_BLANCA_FALABELLA,
            # 'Electro y Tecnología-Línea Blanca',
            #  SUBSECTION_TYPE_CATEGORY_PAGE,
            #  'category/cat7090035/Linea-Blanca'],

            # # CATEGORY PAGES # #
            [bs.REFRIGERATION, 'Refrigeradores',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat3205/Refrigeradores'],
            [bs.WASHING_MACHINES, 'Lavadoras',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'category/cat3136/Lavadoras '],
            [bs.TELEVISIONS, 'TV', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat1012/TV '],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'category/cat2005/Audio'],
            [bs.CELLS, 'Electro y Tecnología-Teléfonos',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'category/cat2018/Telefonos'],

            # # MOSAICS ##
            [bs.LINEA_BLANCA_FALABELLA, 'Electro y Tecnología-Línea Blanca',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat7090035/Linea-Blanca?isPLP=1'],
            [bs.REFRIGERATION, 'Refrigeradores-No Frost',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4074/No-Frost'],
            [bs.REFRIGERATION, 'Refrigeradores-Side by Side',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4091/Side-by-Side'],
            [bs.WASHING_MACHINES, 'Lavadoras', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3136/Lavadoras '],
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
            [bs.TELEVISIONS, 'TV-LED', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat2850014/LED'],
            [bs.TELEVISIONS, 'TV-Smart TV', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3040054/Smart-TV'],
            [bs.TELEVISIONS, 'TV-4K UHD', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3990038/4K-UHD'],
            [bs.TELEVISIONS, 'TV-Televisores OLED', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat2850016/Televisores-OLED'],
            [bs.TELEVISIONS, 'TV', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1012/TV?isPLP=1'],
            [bs.TELEVISIONS, 'Especiales-Televisores Sobre 65"',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat12910024/Televisores-Sobre-65'],
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

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                images = soup.findAll('div', 'fb-hero-carousel-slide')

                for index, image in enumerate(images):
                    picture_array = image.find('picture').findAll('source')
                    destination_urls = [d['href'] for d in image.findAll('a')]
                    destination_urls = list(set(destination_urls))
                    for picture in picture_array:
                        picture_url = picture['srcset'].split(' ')[0]

                        if 'https://www.falabella.com' not in picture_url:
                            picture_url = 'https://www.falabella.com' \
                                          '{}'.format(picture_url)

                        if 'webp' not in picture_url:
                            banners.append({
                                'url': url,
                                'picture_url': picture_url,
                                'destination_urls': destination_urls,
                                'key': picture_url,
                                'position': index+1,
                                'section': section,
                                'subsection': subsection,
                                'type': subsection_type
                            })
                            break
                    else:
                        raise Exception(
                            'No valid banners found for {} in position '
                            '{}'.format(url, index + 1))
            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                with HeadlessChrome(images_enabled=True) as driver:
                    driver.set_window_size(1920, 1080)
                    driver.get(url)

                    pictures = []

                    elements = driver \
                        .find_element_by_class_name('fb-hero-carousel-slides')\
                        .find_elements_by_class_name('fb-slide-image')

                    for element in elements:
                        pictures.append(element.screenshot_as_base64)

                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    images = soup.findAll('div', 'fb-hero-carousel-slide')

                    assert len(images) == len(pictures)

                    for index, image in enumerate(images):
                        picture_array = image.findAll('picture')[-1].findAll(
                            'source')
                        destination_urls = [d['href'] for d in
                                            image.findAll('a')]
                        destination_urls = list(set(destination_urls))

                        for picture in picture_array:
                            key = picture['srcset'].split(' ')[0]
                            if 'webp' not in key:
                                banners.append({
                                    'url': url,
                                    'picture': pictures[index],
                                    'destination_urls': destination_urls,
                                    'key': 'https:{}'.format(key),
                                    'position': index + 1,
                                    'section': section,
                                    'subsection': subsection,
                                    'type': subsection_type
                                })
                                break
                        else:
                            raise Exception(
                                'No valid banners found for {} in position '
                                '{}'.format(url, index + 1))

            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                image_container = soup.find('div',
                                            {'data-module': 'editorial'})

                if not image_container:
                    continue

                picture_url = 'https:{}' \
                    .format(image_container.find('source')['srcset'])
                destination_urls = [image_container.find('a')['href']]
                banners.append({
                    'url': url,
                    'picture_url': picture_url,
                    'destination_urls': destination_urls,
                    'key': picture_url,
                    'position': 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type
                })

        return banners
