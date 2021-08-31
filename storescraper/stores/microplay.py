import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR
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
            'Headphones',
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['computacion', {'categorias': 'mouse'}, 'Mouse'],
            ['gamer', {'categorias': 'mouse-2'}, 'Mouse'],
            ['juegos', {'consolas': 'consola'},
             'VideoGameConsole'],
            ['computacion', {'categorias': 'teclados-3'}, 'Keyboard'],
            ['gamer', {'categorias': 'teclados-4'}, 'Keyboard'],
            ['juegos', {'plataformas': 'pc',
                        'accesorios': 'mouse-teclados'},
             'Keyboard'],
            ['computacion', {'categorias': 'audifonos-14'},
             'Headphones'],
            ['gamer', {'categorias': 'audifonos-2'}, 'Headphones'],
            ['gamer', {'categorias': 'sillas-gamer-2'}, GAMING_CHAIR]
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
                    print(catalogo_name, filters)
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
                product_containers = soup.findAll('div', 'card__item')

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

        if 'Producto no disponible' in page_source:
            return []

        name = soup.find('h1').text.strip()
        sku = re.search(r'ecomm_prodid: (\d+)', page_source).groups()[0]

        price_container = soup.find('span', 'text_web')

        if price_container:
            price = remove_words(
                price_container.find('strong').find('p').nextSibling)
        else:
            price_container = soup.find('span', 'oferta')
            if not price_container:
                return []
            price = remove_words(price_container.find('b').text)

        price = Decimal(price)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'box-descripcion'})))
        picture_urls = [tag['href'] for tag in
                        soup.find('div', 'owl-carousel').findAll(
                            'a', 'fancybox')]

        if soup.find('span', 'fecha-lanzamiento'):
            stock = 0
        else:
            stock = -1

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
