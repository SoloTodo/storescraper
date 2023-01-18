from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import CELL, NOTEBOOK, OVEN, REFRIGERATOR, \
    STEREO_SYSTEM, TELEVISION, WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class LaCuracao(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR,
            NOTEBOOK,
            WASHING_MACHINE,
            OVEN,
            TELEVISION,
            STEREO_SYSTEM,
            CELL,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['3074457345616720730', REFRIGERATOR],
            ['3074457345616813209', NOTEBOOK],
            ['3074457345616720731', WASHING_MACHINE],
            ['3074457345616720732', OVEN],
            ['3074457345616720729', TELEVISION],
            ['3074457345616720733', STEREO_SYSTEM],
            ['3074457345616751193', CELL],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                index = str(12*(page - 1) + 1)
                url_webpage = 'https://www.lacuracao.pe/webapp/wcs/stores/se' \
                    'rvlet/CategoryNavigationResultsGridScrollView?categoryI' \
                    'd={}&storeId=10151&beginIndex={}&pageSize=12'.format(
                        url_extension, index)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = re.search(r'id="ProductInfoName_(\d*)"',
                        response.text).groups()[0].split('_')[-1]

        name = soup.find('input', {'id': f'ProductInfoName_{key}'})[
            'value'].strip()
        sku = soup.find('span', {'id': f'product_SKU_{key}'}).text.split(
            'SKU:')[-1].strip()
        price = Decimal(str(soup.find(
            'input', {'id': f'ProductInfoPrice_{key}'}
        )['value']).replace(",", ""))

        if soup.find(
                'input',
                {'id': 'validatePopUpPickupStoreStockZero'})['value'] == "1":
            stock = 0
        else:
            stock = -1

        pictures_data = soup.find(
            'div', {'id': 'ProductAngleProdImagesAreaProdList'})
        if pictures_data:
            picture_urls = ['https://www.lacuracao.pe' + tag['src'].replace(
                '200x310', '656x1000') for tag in pictures_data.findAll('img')]
        else:
            picture_urls = []

        description = html_to_markdown(
            soup.find('div', {'id': f'product_longdescription_{key}'}).text)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'PEN',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
