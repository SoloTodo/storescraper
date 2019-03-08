import json
import re
import urllib
import time

from bs4 import BeautifulSoup
from decimal import Decimal
from urllib.parse import urlparse, parse_qs, urlencode

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy, HeadlessChrome
from storescraper import banner_sections as bs


class AbcDin(Store):
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
            'VideoGameConsole',
            'AllInOne',
            'WaterHeater',
            'Wearable',
            'Headphones',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        ajax_resources = [
            ['10076', 'Notebook'],
            ['10003', 'Television'],
            ['10075', 'Tablet'],
            ['10025', 'Refrigerator'],
            ['10026', 'Refrigerator'],
            ['10027', 'Refrigerator'],
            ['10028', 'Refrigerator'],
            ['10029', 'Refrigerator'],
            ['10078', 'Printer'],
            ['29587', 'Printer'],
            ['10041', 'Oven'],
            ['10042', 'Oven'],
            ['10043', 'VacuumCleaner'],
            ['10031', 'WashingMachine'],
            ['10032', 'WashingMachine'],
            ['10033', 'WashingMachine'],
            ['24553', 'Cell'],  # Smartphones
            ['10018', 'Camera'],
            ['37051', 'StereoSystem'],  # Parlantes portátiles
            ['44051', 'StereoSystem'],  # Accesorios audio
            ['10007', 'StereoSystem'],  # Minicomponentes
            ['10008', 'StereoSystem'],  # Microcomponentes
            ['10009', 'StereoSystem'],  # Home Theater
            ['10010', 'StereoSystem'],  # Radios
            ['10012', 'StereoSystem'],  # Reproductores de Música
            ['10501', 'StereoSystem'],  # Tornamesas
            ['10004', 'OpticalDiskPlayer'],
            ['10082', 'UsbFlashDrive'],
            # ['14008', 'VideoGameConsole'],  # PS3
            ['14001', 'VideoGameConsole'],  # PS4
            # ['14009', 'VideoGameConsole'],  # Xbox 360
            ['14005', 'VideoGameConsole'],  # Xbox One
            ['14011', 'VideoGameConsole'],  # Switch
            ['14012', 'VideoGameConsole'],  # 3DS
            ['14011', 'VideoGameConsole'],  # Wii U
            ['10077', 'AllInOne'],
            ['10065', 'WaterHeater'],
            ['10061', 'SpaceHeater'],  # Estufas electricas
            ['10063', 'SpaceHeater'],  # Estufas a lena
            ['24055', 'Wearable'],
            ['10013', 'Headphones'],
        ]

        discovered_urls = []

        session = session_with_proxy(extra_args)

        for category_id, local_category in ajax_resources:
            if local_category != category:
                continue

            url = 'https://www.abcdin.cl/tienda/ProductListingView?' \
                  'searchTermScope=&searchType=10&filterTerm=' \
                  '&langId=-1000&advancedSearch=' \
                  '&sType=SimpleSearch&gridPosition=' \
                  '&metaData=&manufacturer=' \
                  '&ajaxStoreImageDir=%2Fwcsstore%2FABCDIN%2F' \
                  '&resultCatEntryType=&catalogId=10001&searchTerm=' \
                  '&resultsPerPage=12' \
                  '&emsName=Widget_CatalogEntryList_701_1974' \
                  '&facet=&categoryId={0}' \
                  '&storeId=10001&enableSKUListView=false' \
                  '&disableProductCompare=false' \
                  '&ddkey=ProductListingView_8_-2011_1974&filterFacet=' \
                  '&pageSize=1000'.format(category_id)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            products_grid = soup.find('ul', 'grid_mode')

            if not products_grid:
                raise Exception('Empty category path: {} - {}'.format(
                    category, category_id))

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
                discovered_urls.append(product_url)

        return discovered_urls

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
            picture_urls=picture_urls
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

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                with HeadlessChrome(images_enabled=True) as driver:
                    driver.set_window_size(1920, 1080)
                    driver.get(url)

                    elements = driver.find_elements_by_class_name('homeHero')

                    time.sleep(1)

                    controls = driver\
                        .find_element_by_class_name('pageControl')\
                        .find_elements_by_tag_name('a')

                    assert len(elements) == len(controls)

                    for index, element in enumerate(elements):
                        control = controls[index]
                        control.click()
                        time.sleep(2)
                        picture = element.screenshot_as_base64
                        key_container = element\
                            .value_of_css_property('background-image')

                        key = re.search(r'url\("(.*?)"\)', key_container)\
                            .group(1)

                        destination_urls = \
                            [element.find_element_by_tag_name('a')
                                .get_attribute('href')]

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
                if elements:
                    for index, element in enumerate(elements):
                        picture_url = element.find('img')['src']
                        destination_urls = ['https://www.abcdin.cl' +
                                            element.find('a')['href']]
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
