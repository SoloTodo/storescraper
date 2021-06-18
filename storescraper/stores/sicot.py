import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MONITOR, TABLET, GAMING_CHAIR, \
    PRINTER, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Sicot(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MONITOR,
            TABLET,
            GAMING_CHAIR,
            PRINTER,
            ALL_IN_ONE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebook', NOTEBOOK],
            ['chromebook', NOTEBOOK],
            ['aio', ALL_IN_ONE],
            ['monitores', MONITOR],
            ['tablets', TABLET],
            ['gamer', GAMING_CHAIR],
            ['impresoras', PRINTER]
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

                url_webpage = 'https://www.sicot.cl/collection/{}' \
                              '?page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'bs-product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://www.sicot.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_container = soup.find('main', 'bs-main').find(
            'script').text.strip()
        json_container = json.loads(
            re.search(r"window.INIT.products.push\(([\s\S]+)\);",
                      json_container).groups()[0])
        name = json_container['product']['title']
        picture_urls = [tag['data-lazy'] for tag in
                        soup.find('section', 'col-12 relative').findAll('img')]
        description = html_to_markdown(
            json_container['product']['description'])

        products = []

        for variant in json_container['variants']:
            variant_name = '{} {}'.format(name, variant['title']).strip()
            part_number = variant['sku']
            sku = str(variant['id'])
            stock = int(
                variant['stock'][0]['quantityAvailable'])
            price = Decimal(variant['finalPrice'])
            p = Product(
                variant_name,
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
                part_number=part_number,
                picture_urls=picture_urls,
                description=description
            )
            products.append(p)
        return products
