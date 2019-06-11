import json
import random
import re
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Johnson(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'WashingMachine',

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['51639113', 'Refrigerator'],
            ['51639109', 'Refrigerator'],
            ['51639110', 'Refrigerator'],
            ['51799622', 'Refrigerator'],
            ['51799611', 'WashingMachine'],
            ['51799612', 'WashingMachine'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for path, local_category in category_paths:
            if category != local_category:
                continue

            category_url = 'https://www.johnson.cl/webapp/wcs/stores/servlet' \
                           '/AjaxCatalogSearchResultView?sType=SimpleSearch&' \
                           'pageSize=1000&storeId=11351&categoryId={}&'.format(
                               path)
            print(category_url)
            soup = BeautifulSoup(session.get(
                category_url, timeout=30).text, 'html.parser')

            product_containers = soup.findAll('div', 'boxProduct')

            if not product_containers:
                raise Exception('Empty category: {} - {}'.format(
                    category, path))

            for cell in product_containers:
                product_link = cell.find('a', {'id': 'myBtn'})

                product_js = product_link['onclick']
                product_id = re.search(
                    r"showPopup\('(\d+)'", product_js)
                if not product_id:
                    # "Producto con precio pendiente"
                    continue
                product_id = product_id.groups()[0]
                product_url = 'https://www.johnson.cl/tienda/ProductDisplay?' \
                              'storeId=11351&productId=' + product_id
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        page_source = session.get(url, timeout=30).text
        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('img', {
                'src': 'https://paris.scene7.com/is/image/Cencosud/'
                       'Error%5FGenerico%5FB?$full%2Djpeg$'}):
            print('Error generico found (#1)')
            return []

        if soup.find('h1', {'role': 'main'}):
            print('Error generico found (#2)')
            return []

        name = soup.find('h1', {'id': 'catalog_link'})

        if not name:
            print('No name found')
            return []

        name = name.text.strip()

        sku = soup.find('div', {'id': 'detalles-sku'}).text.replace(
            'SKU: ', '').strip()
        normal_price = re.search(
            r"var offerPrice_DL = '(\d*)'", page_source).groups()[0]
        if not normal_price:
            return []

        normal_price = Decimal(normal_price)

        offer_price = re.search(
            r"var tcPrice_DL = '(\d*)'", page_source).groups()[0]
        if offer_price:
            offer_price = Decimal(offer_price)
            if offer_price > normal_price:
                offer_price = normal_price
        else:
            offer_price = normal_price

        stock = re.search(
            r"var itemQuantity_DL = '(.+)'",
            page_source)
        if stock:
            stock = int(stock.groups()[0].replace('.', ''))
        else:
            stock = 0

        description = html_to_markdown(str(soup.find('div', 'description')))

        image_id = re.search(
            r"var field3_DL = '(.*)';", page_source).groups()[0]

        if not image_id:
            image_id = re.search(
                r"var partNumber_DL = '(.+)';", page_source).groups()[0]

        print(image_id)
        pictures_resource_url = 'https://imagenes.paris.cl/is/image/' \
                                'Cencosud/{}?req=set,json'.format(image_id)

        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      session.get(pictures_resource_url).text).groups()[0])
        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https://imagenes.paris.cl/is/image/{}?scl=1.0' \
                          ''.format(picture_entry['i']['n'])
            picture_urls.append(picture_url)

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
            picture_urls=picture_urls
        )

        return [p]
