import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Microplay(Store):
    @classmethod
    def categories(cls):
        return [
            'Mouse',
            'VideoGameConsole',
            'Keyboard',
            'KeyboardMouseCombo',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['computacion', {'categorias': 'mouse'}, 'Mouse'],
            ['gamer', {'categorias': 'mouse-2'}, 'Mouse'],
            ['juegos', {'plataformas': 'xbox-one', 'consolas': 'consola'},
             'VideoGameConsole'],
            ['juegos', {'plataformas': 'nintendo-3ds', 'consolas': 'consola'},
             'VideoGameConsole'],
            ['juegos',
             {'plataformas': 'nintendo-switch', 'consolas': 'consola'},
             'VideoGameConsole'],
            ['computacion', {'categorias': 'teclados-3'}, 'Keyboard'],
            ['gamer', {'categorias': 'teclados-4'}, 'Keyboard'],
            ['juegos', {'plataformas': 'pc',
                        'accesorios': 'mouse-teclados'},
             'Keyboard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        for catalogo_name, filters, local_category in category_paths:
            if local_category != category:
                continue
            p = 1

            while True:
                if p > 20:
                    raise Exception('Page overflow')

                request_pars = {
                    'familia': {'catalogo': catalogo_name},
                    'filtro': filters,
                    'control': []
                }
                request_pars = json.dumps(request_pars)

                params = {
                    'pars': request_pars,
                    'page': p
                }
                data = urllib.parse.urlencode(params)
                response = session.post('https://www.microplay.cl/productos/'
                                        'reader', data)

                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'producto')

                if not product_containers:
                    break

                for container in product_containers:
                    product_url = 'https://www.microplay.cl' + \
                                  container.find('a')['href']
                    product_urls.append(product_url)

                p += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = re.search('ecomm_prodid: (\d+)', page_source).groups()[0]

        with_stock_web = soup.find('a', 'btn-agregar2')
        with_stock_store = soup.find('a', {'href': '#div_sucursales'})

        if with_stock_web or with_stock_store:
            stock = -1
        else:
            stock = 0

        price = re.search('ecomm_totalvalue: (\d+).00',
                          page_source).groups()[0]
        price = Decimal(price)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'box-descripcion'})))
        picture_urls = [tag['href'] for tag in
                        soup.find('div', 'owl-carousel').findAll(
                            'a', 'fancybox')]

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
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
