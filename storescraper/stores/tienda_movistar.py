import json
import logging
import re
import urllib

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import HEADPHONES, TABLET, CELL, MOUSE, WEARABLE, \
    VIDEO_GAME_CONSOLE, STEREO_SYSTEM
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
            WEARABLE,
            VIDEO_GAME_CONSOLE,
            STEREO_SYSTEM
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['celulares', [CELL], 'Celulares', 1],
            ['outlet/celulares-reacondicionados', [CELL],
             'Celulares Reacondicionados', 1],
            ['outlet.html', [CELL], 'Outlet', 1],
            ['tablets', [TABLET], 'Tablets', 1],
            ['outlet/tablets', [TABLET], 'Outlet Tablets', 1],
            ['audifonos', [HEADPHONES], 'Audífonos', 1],
            ['smartwatch', [WEARABLE], 'SmartWatch', 1],
            ['outlet/smartwatch', [WEARABLE], 'Outlet Smartwatch', 1],
            ['gaming/consolas', [VIDEO_GAME_CONSOLE], 'Consolas de Videojuegos', 1],
            ['accesorios/parlantes-bluetooth', [STEREO_SYSTEM],
             'Parlantes Bluetooth', 1],
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
                category_url = 'https://catalogo.movistar.cl/tienda/{}/?p={}'.format(category_path, page)
                print(category_url)

                if page >= 80:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                items = soup.findAll('li', 'product')

                if not items:
                    if page == 1:
                        logging.warning('Empty category: ' + category_url)
                    break

                empty_page = True

                for cell_item in items:
                    if not cell_item.find('div', 'sin-stock'):
                        empty_page = False
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

                if empty_page:
                    break

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

        stock_match = re.search(r'stockMagento: (\d+),', page_source)
        stock = int(stock_match.groups()[0])

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
