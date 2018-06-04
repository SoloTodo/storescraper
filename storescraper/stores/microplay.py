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
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).string.strip()
        with_stock_web = soup.find('a', 'btn-agregar')

        if with_stock_web:
            sku = with_stock_web['data-product_id']
        else:
            sku_container = soup.find('a', 'consulta_stock')
            if sku_container:
                sku = sku_container['rel'][0]
            else:
                return []

        if with_stock_web:
            stock = -1
        else:
            params = {
                'id': sku,
                'preferencia': ''
            }
            data = urllib.parse.urlencode(params)
            session.headers[
                'Content-Type'] = 'application/x-www-form-urlencoded'
            response = session.post(
                'https://www.microplay.cl/sucursales/producto', data=data)

            stock_soup = BeautifulSoup(response.text)

            if stock_soup.find('a', 'tooltip_sucursales'):
                stock = -1
            else:
                stock = 0

        price = re.search(
            r'(\d+\.\d+)', soup.find('div', 'precios_usado').text).groups()[0]
        price = Decimal(remove_words(price))

        description = html_to_markdown(
            str(soup.find('div', {'id': 'box-descripcion'})))
        picture_urls = [tag['href'] for tag in
                        soup.find('div', 'galeria').findAll('a', 'fancybox')]

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
