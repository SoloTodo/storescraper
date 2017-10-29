import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class OrtizYOrtega(Store):
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
            ['54', 'Refrigerator'],
            ['55', 'Refrigerator'],
            ['60', 'AirConditioner'],
            ['92', 'WaterHeater'],
            ['53', 'WashingMachine'],
            # ['61', 'WashingMachine'],
            ['62', 'WashingMachine'],
            ['71', 'Stove'],
            ['83', 'Stove'],
            ['508', 'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                url = 'http://www.ortizyortega.com.ar/index.pl?' \
                      'defaultCommand=getListItems&_a=getListItems&' \
                      '_c=catalogueFront&mod=catalogueFront&id={0}&' \
                      'productOrderBy=&productOrderBySort=&page={1}&' \
                      '%2Fcatalogue%2Fsearch.html%3FsearchField__' \
                      'category__id_node__equal={0}'.format(
                        category_path, page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                containers = soup.findAll('div', 'box_prod_listado')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                for container in containers:
                    url = 'http://www.ortizyortega.com.ar' + \
                          urllib.parse.quote(container.findAll(
                              'a')[1]['href'])
                    product_urls.append(url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')
        sku = soup.find('input', {'id': 'id'})['value'].strip()

        price_string = soup.find('span', 'text_precio_detalle_num').text
        price = Decimal(price_string.replace('$', '').replace(',', '.'))

        stock = int(re.search(r"verficarStock\('(\d+)",
                              page_source).groups()[0])

        description = html_to_markdown(
            str(soup.find('div', 'cont_especificaciones_detalle')))

        picture_urls = [soup.find('a', {'id': 'image_product'})['href']]
        soup = soup.find('div', 'cont_der_ficha_prod_detalle')
        name = soup.find('h1').text.strip()

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
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
