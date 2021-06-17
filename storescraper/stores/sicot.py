import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MONITOR, TABLET, GAMING_CHAIR, \
    PRINTER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Sicot(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MONITOR,
            TABLET,
            GAMING_CHAIR,
            PRINTER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebook', NOTEBOOK],
            ['chromebook', NOTEBOOK],
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
        part_number = json_container['variants'][0]['sku']
        sku = str(json_container['variants'][0]['id'])
        stock = int(
            json_container['variants'][0]['stock'][0]['quantityAvailable'])
        price = Decimal(json_container['variants'][0]['finalPrice'])
        picture_urls = [tag['data-lazy'] for tag in
                        soup.find('section', 'col-12 relative').findAll('img')]
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
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
