import re

import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from urllib.parse import urlparse, parse_qs, urlencode

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words


class AbcDin(Store):
    @classmethod
    def product_types(cls):
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
    def discover_urls_for_product_type(cls, product_type, extra_args=None):
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
            ['24553', 'Cell'],
            ['10018', 'Camera'],
            ['10007', 'StereoSystem'],
            ['10008', 'StereoSystem'],
            ['10004', 'OpticalDiskPlayer'],
            ['10009', 'HomeTheater'],
            ['10082', 'UsbFlashDrive'],
            ['16010', 'VideoGameConsole'],  # PS3
            ['16013', 'VideoGameConsole'],  # PS4
            ['16004', 'VideoGameConsole'],  # Xbox 360
            ['16007', 'VideoGameConsole'],  # Xbox One
            ['14012', 'VideoGameConsole'],  # 3DS
            ['14011', 'VideoGameConsole'],  # Wii U
            ['10077', 'AllInOne'],
            ['10065', 'WaterHeater'],
        ]

        discovered_urls = []

        for category_id, ptype in ajax_resources:
            if ptype != product_type:
                continue

            url = 'http://www.abcdin.cl/tienda/ProductListingView?' \
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

            soup = BeautifulSoup(requests.get(url).text, 'html.parser')
            product_cells = soup.find('ul', 'grid_mode').findAll('li')

            for idx, product_cell in enumerate(product_cells):
                product_url = product_cell.find('a')['href']
                product_url = product_url.replace(
                    'abc-live.prod.coc.ibmcloud.com', 'www.abcdin.cl')
                product_url = product_url.replace('http://', 'https://')

                if 'ProductDisplay' in product_url:
                    parsed_product = urlparse(product_url)
                    parameters = parse_qs(parsed_product.query)

                    parameters = {
                        k: v for k, v in parameters.items()
                        if k in ['urlRequestType', 'productId', 'langId',
                                 'storeId']}

                    newqs = urlencode(parameters, doseq=True)

                    product_url = \
                        'https://www.abcdin.cl/tienda/ProductDisplay?' + newqs

                discovered_urls.append(product_url)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, product_type=None, extra_args=None):
        product_webpage = requests.get(url)
        soup = BeautifulSoup(product_webpage.text, 'html.parser')

        if soup.find('div', {'id': 'errorPage'}):
            return []

        try:
            name = soup.find(
                'span', {'itemprop': 'name'}).string.strip()
        except AttributeError:
            return []

        prices_containers = soup.findAll('div', 'detailprecioBig')

        if not prices_containers:
            return []

        if soup.findAll('div', {'id': 'productPageAdd2Cart'}):
            stock = -1
        else:
            stock = 0

        normal_price = prices_containers[1].text
        normal_price = Decimal(remove_words(normal_price))

        if len(prices_containers) == 3:
            offer_price = Decimal(remove_words(prices_containers[2].text))
        else:
            offer_price = normal_price

        sku = soup.find('meta', {'name': 'pageIdentifier'})['content']
        description = soup.find(
            'p', attrs={'id': re.compile(r'product_longdescription_.*')}).text

        product = Product(
            name,
            cls.__name__,
            product_type,
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
            cell_monthly_payment=None
        )

        return [product]
