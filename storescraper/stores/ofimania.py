import json
import logging
import re
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, HEADPHONES, KEYBOARD, \
    NOTEBOOK, TABLET, CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Ofimania(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            HEADPHONES,
            KEYBOARD,
            NOTEBOOK,
            TABLET,
            CELL
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computacion/almacenamiento', SOLID_STATE_DRIVE],
            ['computacion/audifonos', HEADPHONES],
            ['computacion/mouse-y-teclado', KEYBOARD],
            ['computacion/notebooks', NOTEBOOK],
            ['computacion/tablets', TABLET],
            ['telefonia', CELL]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://ofimania.cl/categoria-producto/' \
                              '{}/page/{}/?per_page=36' \
                              '&_pjax=.main-page-wrapper'.format(
                                url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'products')
                if not product_containers or soup.find('h3', 'title'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll(
                        'div', 'product-grid-item'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, allow_redirects=False)
        if response.status_code == 301:
            return []

        currrency_data = json.loads(re.search(
            r'var woocs_current_currency = (.+);', response.text).groups()[0])
        assert currrency_data['name'] == 'CLP'
        soup = BeautifulSoup(response.text, 'html.parser')
        product_data = json.loads(
            soup.findAll('script', {'type': 'application/ld+json'})[1].text)[
            '@graph'][1]
        description = html_to_markdown(product_data['description'])

        if 'pedido' in description.lower():
            stock = 0
        elif soup.find('form', 'variations_form'):
            json_container = json.loads(soup.find('form', 'variations_form')[
                                            'data-product_variations'])
            stock_tag = BeautifulSoup(json_container[0]['availability_html'],
                                      'html.parser')

            if stock_tag.text.strip() == 'Agotado' or \
                    not stock_tag.text.strip():
                stock = 0
            else:
                stock = int(stock_tag.text.split()[0])
        elif soup.find('p', 'available-on-backorder'):
            stock = 0
        elif soup.find('p', 'stock out-of-stock'):
            stock = 0
        elif soup.find('p', 'stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = -1

        sku = product_data['sku']
        name = product_data['name']
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        pricing_data = product_data['offers'][0]
        if 'price' in pricing_data:
            orig_price = Decimal(pricing_data['price'])
        else:
            orig_price = Decimal(pricing_data['lowPrice'])

        if pricing_data['priceCurrency'] == 'USD':
            price = (orig_price * Decimal(
                str(currrency_data['rate']))).quantize(0)
        elif pricing_data['priceCurrency'] == 'CLP':
            price = orig_price
        else:
            raise Exception('Invalid currency')

        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div',
                                  'woocommerce-product-gallery').findAll(
                            'img')
                        if validators.url(tag['src'])]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
