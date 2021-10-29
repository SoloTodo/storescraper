import json
import re
import urllib

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import HEADPHONES, TABLET, CELL, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words


class TiendaMovistar(Store):
    # preferred_discover_urls_concurrency = 1
    # preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            CELL,
            TABLET,
            HEADPHONES,
            MOUSE
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['smartphones-liberados.html', [CELL],
             'Smartphones liberados', 1],
            ['outlet.html', [CELL], 'Outlet', 1],
            ['tablets.html', [TABLET], 'Tablets', 1],
            ['accesorios.html', [HEADPHONES], 'Accesorios', 1],
            ['gaming.html', [MOUSE], 'Gaming', 1],
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1
            current_position = 1
            done = False

            while not done:
                category_url = 'https://catalogo.movistar.cl/fullprice/' \
                               'catalogo/{}?p={}'.format(category_path, page)

                if page >= 80:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                items = soup.findAll('div', 'item-producto')

                if not items:
                    raise Exception('Emtpy category: ' + category_url)

                for cell_item in items:
                    product_url = cell_item.find('a')['href']
                    if product_url in product_entries:
                        done = True
                        break

                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': current_position
                    })

                    current_position += 1

                page += 1

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = 'python-requests/2.21.0'
        response = session.get(url)

        if response.status_code == 404:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')

        if not soup.find('body') or \
                not soup.find('h1', {'id': 'nombre-producto'}):
            return []

        name = soup.find('h1', {'id': 'nombre-producto'}).text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()

        ajax_session = session_with_proxy(extra_args)
        ajax_session.headers['user-agent'] = 'python-requests/2.21.0'
        ajax_session.headers['x-requested-with'] = 'XMLHttpRequest'
        ajax_session.headers['content-type'] = \
            'application/x-www-form-urlencoded'

        stock_data = json.loads(ajax_session.post(
            'https://catalogo.movistar.cl/fullprice/stockproducto/validar/',
            'sku=' + sku
        ).text)

        stock = int(stock_data['respuesta']['cantidad'])

        price_container = soup.find('span', 'special-price').find('p')
        price = Decimal(remove_words(price_container.text))

        description = html_to_markdown(str(
            soup.find('div', 'detailed-desktop')))

        if 'seminuevo' in description:
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        picture_urls = [soup.find('meta', {'property': 'og:image'})['content']]

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
            'CLP',
            condition=condition,
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )]
