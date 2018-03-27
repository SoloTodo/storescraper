import json
import re
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal
from urllib.parse import urlparse, parse_qs, urlencode

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


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
            'HomeTheater',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'VideoGameConsole',
            'AllInOne',
            'WaterHeater',
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
            ['10041', 'Oven'],
            ['10042', 'Oven'],
            ['10043', 'VacuumCleaner'],
            ['10031', 'WashingMachine'],
            ['10032', 'WashingMachine'],
            ['10033', 'WashingMachine'],
            ['24553', 'Cell'],  # Smartphones
            ['10018', 'Camera'],
            ['10007', 'StereoSystem'],
            ['10008', 'StereoSystem'],
            ['10004', 'OpticalDiskPlayer'],
            ['10009', 'HomeTheater'],
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
            ['24055', 'Smartwatch'],
        ]

        discovered_urls = []

        session = session_with_proxy(extra_args)

        for category_id, local_category in ajax_resources:
            if local_category != category:
                continue

            print(category_id)

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

        if len(prices_containers) == 3:
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
            picture_urls = ['https://www.abcdin.cl' + picture_pair[1]
                            for picture_pair in sorted_pictures]
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
            part_number=None,
            sku=sku,
            description=description,
            cell_plan_name=None,
            cell_monthly_payment=None,
            picture_urls=picture_urls
        )

        return [product]
