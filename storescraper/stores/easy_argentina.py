import re
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class EasyArgentina(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['14829', 'Refrigerator'],
            ['14831', 'AirConditioner'],
            ['14826', 'WaterHeater'],
            ['14846', 'WashingMachine'],
            ['14825', 'Stove'],
            ['14828', 'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = 'https://www.easy.com.ar/webapp/wcs/stores/servlet/es/' \
                  'easyar/search/AjaxCatalogSearchResultView?' \
                  'searchTermScope=&searchType=1002&filterTerm=&' \
                  'orderBy=&maxPrice=&showResultsPage=true&langId=-5&' \
                  'beginIndex=0&sType=SimpleSearch&metaData=&pageSize=1000&' \
                  'manufacturer=&resultCatEntryType=&catalogId=10051&' \
                  'pageView=image&searchTerm=&minPrice=&categoryId={}&' \
                  'storeId=10151'.format(category_path)

            print(url)
            soup = BeautifulSoup(session.get(url).text, 'html.parser')

            containers = soup.findAll('div', 'thumb-name')

            if not containers:
                raise Exception('Empty category: ' + url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        sku = soup.find('input', {'name': 'catentryCurrent'})['value'].strip()

        name = soup.find('div', 'prod-title').text.strip()

        price_container = soup.find('span', 'price-mas')

        if not price_container:
            price_container = soup.find('span', 'price-e')

        price = Decimal(price_container.text.replace('.', '').replace(
            ',', '.'))

        description = html_to_markdown(
            str(soup.find('div', {'id': 'Description'})))

        picture_urls = ['https://s7d2.scene7.com/is/image/EasyArg/{}'
                        '?scl=1.0'.format(sku)]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
