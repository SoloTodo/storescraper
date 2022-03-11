import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import MONITOR, MOTHERBOARD, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PcCenterTech(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            MOUSE,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-pc', MOTHERBOARD],
            ['perisfericos', MOUSE],
            ['sin-categorizar', MOUSE],
            ['monitores-y-televisores', MONITOR],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.pccentertech.cl/' \
                              'categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                page_not_found = soup.find('title').text
                if 'Página no encontrada' in page_not_found:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a', 'woocommerce-Loop'
                                                      'Product-link')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        product_json = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)

        name = product_json['name']
        key = str(product_json['sku'])
        price = Decimal(product_json['offers'][0]['price'])
        currency = product_json['offers'][0]['priceCurrency']
        description = product_json['description']

        stock_tag = soup.find('p', 'in-stock')
        if stock_tag:
            stock = int(re.search(r'(\d+)', stock_tag.text).groups()[0])
        else:
            stock = -1

        image_list_as = soup.find(
            'div', 'woocommerce-product-gallery').findAll('a')
        image_urls = []
        for a in image_list_as:
            image_urls.append(a['href'])

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
            currency,
            sku=key,
            description=description,
            picture_urls=image_urls
        )

        return [p]
