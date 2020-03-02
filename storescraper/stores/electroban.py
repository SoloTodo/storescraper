from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy

import json


class Electroban(Store):
    base_url = 'https://www.lg.com'
    country_code = 'cl'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'Stove',
            'WashingMachine',
            'AirConditioner'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['15', 'Television'],
            ['14', 'StereoSystem'],
            ['88', 'Cell'],
            ['32', 'Refrigerator'],
            ['6', 'Oven'],
            ['80', 'Oven'],
            ['3', 'Stove'],
            ['9', 'WashingMachine'],
            ['12', 'WashingMachine'],
            ['1', 'AirConditioner']

        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        base_url = 'https://www.eban.com.py/familias_paginacion/{}/{}/'

        for c in category_paths:
            category_path, local_category = c

            if category != local_category:
                continue

            page = 1

            while True:
                url = base_url.format(category_path, page)
                print(url)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    break

                for product in product_containers:
                    product_url = product.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()

        sku_container = soup.find('a', 'single_add_to_cart_button')

        if not sku_container:
            sku = soup.find('input', {'id': 'aux_cod_articulo'})['value']
        else:
            sku = sku_container['href']

        stock_container = soup.find('div', 'availability')

        if not stock_container:
            stock = 0
        else:
            stock = stock_container.find('span').text.split(' ')[0]
            if stock == 'Sin':
                stock = 0
            else:
                stock = int(stock)

        if 'LG' not in name.upper().split(' '):
            stock = 0

        post_data = 'plazo=CONTADO&cod_articulo={}'.format(sku)

        session.headers['Content-Type'] = 'application/x-www-form-urlencoded;'\
                                          ' charset=UTF-8'

        price = soup.find('span', {'id': 'elpreciocentral'})\
            .text.replace('Gs.', '').replace('.', '').strip()

        if not price:
            price = Decimal(session.post(
                'https://www.eban.com.py/ajax/calculo_plazo.php',
                data=post_data).text)
        else:
            price = Decimal(price)

        picture_urls = [soup.find(
            'div', 'thumbnails-single owl-carousel').find('a')['href']]

        return [Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'PYG',
            sku=sku,
            picture_urls=picture_urls
        )]
