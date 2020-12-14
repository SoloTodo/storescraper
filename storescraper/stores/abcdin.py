import json
import logging
import re
import urllib
from collections import defaultdict

import time

from bs4 import BeautifulSoup
from decimal import Decimal
from urllib.parse import urlparse, parse_qs, urlencode
from selenium.common.exceptions import NoSuchElementException

from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy, HeadlessChrome
from storescraper import banner_sections as bs


class AbcDin(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'Notebook',
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
            'VideoGameConsole',
            'AllInOne',
            'WaterHeater',
            'Wearable',
            'Headphones',
            'AirConditioner',
            'Stove',
            'Monitor',
            'Projector',
            'Mouse',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        ajax_resources = [
            # Contains irrelevante TV accesories
            ['10002', ['Television', 'OpticalDiskPlayer'],
             'Electro > TV y Video', 0],
            ['10003', ['Television'],
             'Electro > TV y Video > Televisores LED', 1],
            ['10004', ['OpticalDiskPlayer'],
             'Electro > TV y Video > Reproductores DVD-Blu Ray-TV portátil',
             1],
            # Contains car audio and other irrelevant sections
            ['10006', ['StereoSystem'], 'Electro > Audio', 0],
            ['37051', ['StereoSystem'],
             'Electro > Audio > Parlantes Portátiles', 1],
            ['10007', ['StereoSystem'],
             'Electro > Audio > Minicomponentes', 1],
            ['10008', ['StereoSystem'],
             'Electro > Audio > Microcomponentes', 1],
            ['10009', ['StereoSystem'], 'Electro > Audio > Home Theater', 1],
            ['10012', ['StereoSystem'],
             'Electro > Audio > Reproductores de Música', 1],
            ['10013', ['Headphones'], 'Electro > Audífonos', 1],
            ['10014', ['Headphones'], 'Electro > Audífonos > In Ear', 1],
            ['10015', ['Headphones'], 'Electro > Audífonos > Over Ear', 1],
            ['10016', ['Headphones'], 'Electro > Audífonos > Deportivos', 1],
            ['10024', ['Refrigerator'], 'Línea Blanca > Refrigeradores', 1],
            ['10025', ['Refrigerator'],
             'Línea Blanca > Refrigeradores > Refrigeradores Frio Directo', 1],
            ['10026', ['Refrigerator'],
             'Línea Blanca > Refrigeradores > Refrigeradores No Frost', 1],
            ['10027', ['Refrigerator'],
             'Línea Blanca > Refrigeradores > Refrigeradores Side by Side', 1],
            ['10028', ['Refrigerator'],
             'Línea Blanca > Refrigeradores > Frigobar', 1],
            ['10029', ['Refrigerator'],
             'Línea Blanca > Refrigeradores > Freezers', 1],
            ['10030', ['WashingMachine', 'DishWasher'],
             'Línea Blanca > Lavado y Secado', 0.5],
            ['10031', ['WashingMachine'],
             'Línea Blanca > Lavado y Secado > Lavadoras', 1],
            ['10032', ['WashingMachine'],
             'Línea Blanca > Lavado y Secado > Lavadoras-Secadoras', 1],
            ['10033', ['WashingMachine'],
             'Línea Blanca > Lavado y Secado > Secadoras', 1],
            ['10033', ['WashingMachine'],
             'Línea Blanca > Lavado y Secado > Secadoras', 1],
            ['10034', ['WashingMachine'],
             'Línea Blanca > Lavado y Secado > Centrífugas', 1],
            ['10035', ['DishWasher'],
             'Línea Blanca > Lavado y Secado > Lavavajillas', 1],
            ['10036', ['Stove', 'Oven'],
             'Línea Blanca > Cocinas y Campanas', 0.5],
            ['10037', ['Stove'],
             'Línea Blanca > Cocinas y Campanas > Cocinas', 1],
            ['23552', ['Oven'],
             'Línea Blanca > Cocinas y Campanas > Hornos Empotrables', 1],
            # Contains irrelevant ventiladores, calientacamas
            ['10056', ['AirConditioner', 'SpaceHeater'],
             'Línea Blanca > Climatización', 0],
            ['10058', ['AirConditioner'],
             'Línea Blanca > Climatización > Aire Acondicionado', 1],
            ['42056', ['AirConditioner'],
             'Línea Blanca > Climatización > Purificador de Aire', 1],
            ['10059', ['AirConditioner'],
             'Línea Blanca > Climatización > Enfriadores', 1],
            ['10060', ['SpaceHeater'],
             'Línea Blanca > Climatización > Estufas a Gas', 1],
            ['10061', ['SpaceHeater'],
             'Línea Blanca > Climatización > Estufas Electricas', 1],
            ['10062', ['SpaceHeater'],
             'Línea Blanca > Climatización > Estufas a Parafina', 1],
            ['10063', ['SpaceHeater'],
             'Línea Blanca > Climatización > Estufas a Leña', 1],
            ['10065', ['WaterHeater'],
             'Línea Blanca > Climatización > Calefont', 1],
            ['33051', ['WaterHeater'],
             'Línea Blanca > Climatización > Junkers', 1],
            ['33052', ['WaterHeater'],
             'Línea Blanca > Climatización > Mademsa', 1],
            ['33053', ['WaterHeater'],
             'Línea Blanca > Climatización > Splendid', 1],
            ['47051', ['WaterHeater'],
             'Línea Blanca > Climatización > Neckar', 1],
            ['56052', ['WaterHeater'],
             'Línea Blanca > Climatización > Rheem', 1],
            # Contains all electrodomesticos
            ['10039', ['VacuumCleaner', 'Oven'],
             'Línea Blanca > Electrodomésticos', 0],
            ['10043', ['VacuumCleaner'],
             'Línea Blanca > Electrodomésticos > Aspiradoras y Enceradoras',
             1],
            ['10041', ['Oven'],
             'Línea Blanca > Electrodomésticos > Hornos Eléctricos', 1],
            ['10042', ['Oven'],
             'Línea Blanca > Electrodomésticos > Microondas', 1],
            ['24553', ['Cell'], 'Telefonía > Smartphones', 1],
            ['24554', ['Cell'],
             'Telefonía > Smartphones > Celulares Samsung', 1],
            ['24555', ['Cell'],
             'Telefonía > Smartphones > Celulares Huawei', 1],
            ['24561', ['Cell'],
             'Telefonía > Smartphones > Celulares Motorola', 1],
            ['24558', ['Cell'],
             'Telefonía > Smartphones > Celulares LG', 1],
            ['26051', ['Cell'],
             'Telefonía > Smartphones > Celulares Nokia', 1],
            ['26052', ['Cell'],
             'Telefonía > Smartphones > Iphone', 1],
            ['53051', ['Cell'],
             'Telefonía > Smartphones > Celulares Xiaomi', 1],
            ['25051', ['Cell'],
             'Telefonía > Smartphones > Celulares OWN', 1],
            ['24557', ['Cell'],
             'Telefonía > Smartphones > Celulares Alcatel', 1],
            ['26056', ['Cell'], 'Telefonía > Smartphones > Celulares ZTE', 1],
            ['51552', ['Cell'],
             'Telefonía > Smartphones > Celulares Básicos', 1],
            ['27051', ['Cell'],
             'Telefonía > Smartphones > Celulares Bmobile', 1],
            ['25551', ['Cell'],
             'Telefonía > Smartphones > Celulares Sony', 1],
            ['24556', ['Cell'],
             'Telefonía > Smartphones > Celulares Azumi', 1],
            # Also contains irrelevant accesories
            ['10073', ['MemoryCard', 'StereoSystem'],
             'Telefonía > Accesorios telefonía', 0],
            ['24052', ['MemoryCard'],
             'Telefonía > Accesorios telefonía > Micro SD', 1],
            ['28551', ['StereoSystem'],
             'Telefonía > Accesorios telefonía > Parlantes', 1],
            ['24055', ['Wearable'],
             'Telefonía > Smartwatch', 1],
            ['29552', ['Wearable'],
             'Telefonía > Smartwatch > Smartwatch Samsung', 1],
            ['58052', ['Wearable'],
             'Telefonía > Smartwatch > Smartwatch Xiaomi', 1],
            ['29551', ['Wearable'],
             'Telefonía > Smartwatch > Smartwatch Huawei', 1],
            ['29553', ['Wearable'],
             'Telefonía > Smartwatch > Smartwatch Alcatel', 1],
            ['29554', ['Wearable'],
             'Telefonía > Smartwatch > Smartwatch Kioto', 1],
            ['49052', ['Wearable'],
             'Telefonía > Smartwatch > Smartwatch Microlab', 1],
            ['10076', ['Notebook'],
             'Computación > Notebooks', 1],
            ['29561', ['Notebook'],
             'Computación > Notebooks > Notebooks HP', 1],
            ['29565', ['Notebook'],
             'Computación > Notebooks > Notebooks Lenovo', 1],
            ['50551', ['Notebook'],
             'Computación > Notebooks > Notebooks Gamers', 1],
            ['29563', ['Notebook'],
             'Computación > Notebooks > Macbooks', 1],
            ['29562', ['Notebook'],
             'Computación > Notebooks > Notebooks Acer', 1],
            ['29564', ['Notebook'],
             'Computación > Notebooks > Notebooks ASUS', 1],
            ['10075', ['Tablet'],
             'Computación > Tablets', 1],
            ['29578', ['Tablet'],
             'Computación > Tablets > Tablets Samsung', 1],
            ['46551', ['Tablet'],
             'Computación > Tablets > Tablets Apple', 1],
            ['29574', ['Tablet'],
             'Computación > Tablets > Tablets Kioto', 1],
            ['29575', ['Tablet'],
             'Computación > Tablets > Tablets Lenovo', 1],
            ['29576', ['Tablet'],
             'Computación > Tablets > Tablets Microlab', 1],
            ['29580', ['Tablet'],
             'Computación > Tablets > Tablets Huawei', 1],
            # Also contains inks
            ['29586', ['Printer'],
             'Computación > Impresoras y Multifuncionales', 0],
            ['10078', ['Printer'],
             'Computación > Impresoras y Multifuncionales > Impresoras', 1],
            ['29587', ['Printer'],
             'Computación > Impresoras y Multifuncionales > Multifuncionales',
             1],
            ['10077', ['AllInOne'],
             'Computación > All In One', 1],
            ['30051', ['AllInOne'],
             'Computación > All In One > All In One HP', 1],
            ['30052', ['AllInOne'],
             'Computación > All In One > All In One Lenovo', 1],
            ['30053', ['AllInOne'],
             'Computación > All In One > All In One Apple', 1],
            ['31051', ['Projector', 'Monitor'],
             'Computación > Proyectores', 0.5],
            ['31551', ['Projector'],
             'Computación > Proyectores > Proyectores Epson', 1],
            ['57551', ['Projector'],
             'Computación > Proyectores > Proyectores LG', 1],
            ['58053', ['Monitor'],
             'Computación > Proyectores > Monitores', 1],
            ['10082', ['ExternalStorageDrive', 'UsbFlashDrive', 'MemoryCard'],
             'Computación > Almacenamiento', 0.5],
            ['30061', ['ExternalStorageDrive'],
             'Computación > Almacenamiento > Discos Duros', 1],
            ['30060', ['UsbFlashDrive'],
             'Computación > Almacenamiento > Pendrives', 1],
            ['30062', ['MemoryCard'],
             'Computación > Almacenamiento > Tarjeta Memoria', 1],
            # Also contains other accesories
            ['10079', ['Mouse', 'StereoSystem'],
             'Computación > Accesorios Computación', 0],
            ['10080', ['Mouse'],
             'Computación > Accesorios Computación > Mouse y Teclados', 1],
            ['10081', ['StereoSystem'],
             'Computación > Accesorios Computación > Parlantes y Subwoofer',
             1],
            ['10086', ['VideoGameConsole'],
             'Entretenimiento > Videojuegos', 1],
            ['14001', ['VideoGameConsole'],
             'Entretenimiento > Videojuegos > PS4', 1],
            ['14005', ['VideoGameConsole'],
             'Entretenimiento > Videojuegos > Xbox One', 1],
            ['14011', ['VideoGameConsole'],
             'Entretenimiento > Videojuegos > Nintendo Switch', 1],
            ['14012', ['VideoGameConsole'],
             'Entretenimiento > Videojuegos > Nintendo', 1],
        ]

        discovered_entries = defaultdict(lambda: [])

        session = session_with_proxy(extra_args)

        for category_id, local_categories, section_name, category_weight in \
                ajax_resources:
            if category not in local_categories:
                continue

            url = 'https://www.abcdin.cl/tienda/ProductListingView?' \
                  'searchType=10&langId=-1000&sType=SimpleSearch&' \
                  'ajaxStoreImageDir=%2Fwcsstore%2FABCDIN%2F' \
                  '&catalogId=10001&resultsPerPage=12' \
                  '&emsName=Widget_CatalogEntryList_701_1974' \
                  '&categoryId={}' \
                  '&storeId=10001&enableSKUListView=false' \
                  '&disableProductCompare=false' \
                  '&ddkey=ProductListingView_8_-2011_1974&filterFacet=' \
                  '&pageSize=1000'.format(category_id)
            print(url)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            products_grid = soup.find('ul', 'grid_mode')

            if not products_grid:
                logging.warning('Empty section: {} - {}'.format(
                    category, category_id))
                continue

            product_cells = products_grid.findAll('li')

            for idx, product_cell in enumerate(product_cells):
                product_listed_url = product_cell.find('a')['href']
                if 'ProductDisplay' in product_listed_url:
                    parsed_product = urlparse(product_listed_url)
                    parameters = parse_qs(parsed_product.query)

                    parameters = {
                        k: v for k, v in parameters.items()
                        if k in ['productId', 'storeId']}

                    newqs = urlencode(parameters, doseq=True)

                    product_url = 'https://www.abcdin.cl/tienda/es/abcdin/' \
                                  'ProductDisplay?' + newqs
                else:
                    slug_with_sku = product_listed_url.split('/')[-1]
                    product_url = 'https://www.abcdin.cl/tienda/es/abcdin/'\
                                  + slug_with_sku
                discovered_entries[product_url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

        return discovered_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        keyword = keyword.replace(' ', '+')

        url = 'https://www.abcdin.cl/tienda/ProductListingView?' \
              'ajaxStoreImageDir=%2Fwcsstore%2FABCDIN%2F&searchType=10' \
              '&resultCatEntryType=2&searchTerm={}&resultsPerPage=24' \
              '&sType=SimpleSearch&disableProductCompare=false' \
              '&catalogId=10001&langId=-1000&enableSKUListView=false' \
              '&ddkey=ProductListingView_6_-2011_1410&storeId=10001' \
              '&pageSize=1000'.format(keyword)

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        products_grid = soup.find('ul', 'grid_mode')

        if not products_grid:
            return []

        product_cells = products_grid.findAll('li')

        for product_cell in product_cells:
            product_listed_url = product_cell.find('a')['href']
            if 'ProductDisplay' in product_listed_url:
                parsed_product = urlparse(product_listed_url)
                parameters = parse_qs(parsed_product.query)

                parameters = {
                    k: v for k, v in parameters.items()
                    if k in ['productId', 'storeId']}

                newqs = urlencode(parameters, doseq=True)

                product_url = 'https://www.abcdin.cl/tienda/es/abcdin/' \
                              'ProductDisplay?' + newqs
            else:
                slug_with_sku = product_listed_url.split('/')[-1]
                product_url = 'https://www.abcdin.cl/tienda/es/abcdin/' \
                              + slug_with_sku

            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_content = session.get(url).text
        soup = BeautifulSoup(page_content, 'html.parser')

        if soup.find('div', {'id': 'errorPage'}):
            return []

        try:
            name = soup.find(
                'span', {'itemprop': 'name'}).text.strip()
        except AttributeError:
            return []

        page_content = page_content.replace(name, urllib.parse.quote(name))
        soup = BeautifulSoup(page_content, 'html.parser')

        prices_containers = soup.findAll('div', 'detailprecioBig')

        if not prices_containers:
            return []

        if soup.findAll('div', {'id': 'productPageAdd2Cart'}):
            stock = -1
        else:
            stock = 0

        if len(prices_containers) == 1:
            return []

        normal_price = prices_containers[1].text

        if not remove_words(normal_price).strip():
            return []

        normal_price = Decimal(remove_words(normal_price))

        if len(prices_containers) >= 3:
            offer_price = Decimal(remove_words(prices_containers[2].text))
        else:
            offer_price = normal_price

        if offer_price > normal_price:
            offer_price = normal_price

        sku = soup.find('meta', {'name': 'pageIdentifier'})['content']

        description = html_to_markdown(str(soup.find(
            'p', attrs={'id': re.compile(r'product_longdescription_.*')})),
            baseurl='https://www.abcdin.cl'
        )

        pictures_data = json.loads(soup.find('div', 'jsonProduct').text)
        pictures_dict = pictures_data[0]['Attributes']

        if 'ItemAngleFullImage' in pictures_dict:
            sorted_pictures = sorted(
                pictures_dict['ItemAngleFullImage'].items(),
                key=lambda pair: int(pair[0].replace('image_', '')))
            picture_urls = [
                'https://www.abcdin.cl' + picture_pair[1].replace(' ', '')
                for picture_pair in sorted_pictures
            ]
        else:
            picture_urls = [
                'https://www.abcdin.cl' +
                soup.find('img', {'id': 'productMainImage'})['src']
            ]

        flixmedia_id = None
        video_urls = None
        flixmedia_tag = soup.find(
            'script', {'src': '//media.flixfacts.com/js/loader.js'})

        if flixmedia_tag:
            try:
                flixmedia_id = flixmedia_tag['data-flix-mpn']
                video_urls = flixmedia_video_urls(flixmedia_id)
            except KeyError:
                pass

        if 'reacondicionado' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        has_virtual_assistant = \
            'cdn.livechatinc.com/tracking.js' in page_content

        product = Product(
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
            video_urls=video_urls,
            flixmedia_id=flixmedia_id,
            condition=condition,
            has_virtual_assistant=has_virtual_assistant
        )

        return [product]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.abcdin.cl/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [bs.LINEA_BLANCA_ABCDIN, 'Línea Blanca AbcDin',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'tienda/es/abcdin/linea-blanca'],
            [bs.TELEVISIONS, 'Electro', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'tienda/es/abcdin/tv-audio'],
            [bs.CELLS, 'Telefonía', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
             'tienda/es/abcdin/celulares'],
            [bs.REFRIGERATION, 'Refrigeradores', bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/linea-blanca/refrigeradores'],
            [bs.REFRIGERATION, 'Refrigeradores No Frost',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/linea-blanca/refrigeradores/'
             'refrigeradores-no-frost'],
            [bs.REFRIGERATION, 'Refrigeradores Side by Side',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/linea-blanca/refrigeradores/'
             'refrigeradores-side-by-side'],
            [bs.WASHING_MACHINES, 'Lavado y Secado', bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/linea-blanca/lavado-secado'],
            [bs.WASHING_MACHINES, 'Lavadoras', bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/linea-blanca/lavado-secado/lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/linea-blanca/lavado-secado/'
             'lavadoras-secadoras'],
            [bs.TELEVISIONS, 'Electro', bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/tv-audio'],
            [bs.TELEVISIONS, 'Televisores LED', bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/tv-audio/televisores-video/televisores-led'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/tv-audio/audio'],
            [bs.AUDIO, 'Minicomponentes', bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/tv-audio/audio/minicomponentes'],
            [bs.AUDIO, 'Home Theater', bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/tv-audio/audio/home-theater'],
            [bs.CELLS, 'Smartphones', bs.SUBSECTION_TYPE_MOSAIC,
             'tienda/es/abcdin/celulares/smartphones']
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                with HeadlessChrome(images_enabled=True) as driver:
                    driver.set_window_size(1920, 1080)
                    driver.get(url)

                    time.sleep(10)

                    elements = driver.find_elements_by_class_name(
                        'slide-static')

                    controls = driver\
                        .find_element_by_class_name('pageControl')\
                        .find_elements_by_tag_name('a')

                    assert len(elements) == len(controls)

                    for index, element in enumerate(elements):
                        modal_button = driver \
                            .find_elements_by_class_name('btn-close-pop-up')

                        if modal_button:
                            try:
                                modal_button[0].click()
                                time.sleep(2)
                            except Exception:
                                # Most likely button not interactable
                                continue

                        print('wut')

                        control = controls[index]
                        control.click()
                        time.sleep(2)
                        picture = element.screenshot_as_base64
                        key_container = element\
                            .value_of_css_property('background-image')

                        key = re.search(r'url\("(.*?)"\)', key_container)\
                            .group(1)

                        try:
                            destination_urls = [
                                element.find_element_by_tag_name('a')
                                .get_attribute('href')]
                        except NoSuchElementException:
                            destination_urls = []

                        banners.append({
                            'url': url,
                            'picture': picture,
                            'destination_urls': destination_urls,
                            'key': key,
                            'position': index + 1,
                            'section': section,
                            'subsection': subsection,
                            'type': subsection_type
                        })

            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                # STATIC BANNER
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                banner = soup.find('a', {'data-type': 'huincha'})
                if banner:
                    picture_url = banner.find('img')['src']
                    destination_urls = ['https://www.abcdin.cl'+banner['href']]
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

                # CAROUSEL
                elements = soup.findAll('div', 'homeHero')
                for index, element in enumerate(elements):
                    picture_url = element.find('img')['src']
                    url_suffix = element.find('a')

                    if not url_suffix:
                        destination_urls = []
                    else:
                        destination_urls = ['https://www.abcdin.cl' +
                                            url_suffix['href']]
                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'destination_urls': destination_urls,
                        'key': picture_url,
                        'position': index + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })

            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                banner = soup.find('a', {'data-type': 'huincha'})
                if not banner:
                    banner = soup.find('div', 'homeHero')
                    if banner:
                        banner = banner.find('a')
                if banner:
                    picture_url = banner.find('img')['src']
                    destination_urls = [
                        'https://www.abcdin.cl' + banner['href']]
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
