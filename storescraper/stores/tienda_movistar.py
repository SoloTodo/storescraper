import json
import re
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words


class TiendaMovistar(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Tablet'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('smartphones-liberados.html', 'Cell'),
            ('outlet.html', 'Cell'),
            ('tablets.html', 'Tablet'),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                category_url = 'https://catalogo.movistar.cl/fullprice/' \
                               'catalogo/{}?p={}'.format(category_path, page)
                print(category_url)

                if page >= 20:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                items = soup.findAll('div', 'item-producto')

                if not items:
                    raise Exception('Emtpy category: ' + category_url)

                for cell_item in items:
                    product_url = cell_item.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', {'id': 'nombre-producto'}).text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()
        stock_button = soup.find('button', 'btn-sin-stock')

        if 'style' in stock_button.attrs:
            stock = -1
        else:
            stock = 0

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
