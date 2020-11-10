import json
import logging
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from storescraper.categories import REFRIGERATOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LitnorHogar(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['lg', REFRIGERATOR]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 0
            while True:
                url_webpage = 'https://www.litnorhogar.com.uy/buscador?b={}' \
                              '&page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'views-row')
                if not product_containers:
                    if page == 0:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('div', 'field').find('a')[
                        'href']
                    product_urls.append(
                        'https://www.litnorhogar.com.uy' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'title').text.strip()
        sku = soup.find('div', 'node')['id'].split("-")[-1]
        response = requests.post(
            'https://www.litnorhogar.com.uy/uc_out_of_stock/query',
            data='form_ids%5B%5D=uc-product-add-to-cart-form-'
                 '{}&node_ids%5B%5D={}'.format(sku, sku),
            headers={'content-type': 'application/x-www-form-urlencoded'})
        stock = int(list(json.loads(response.content).values())[0])
        price = Decimal(
            soup.find('span', 'uc-price').text.strip().split()[1].replace('.',
                                                                          ''))
        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'field').findAll('img')]
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
            'USD',
            sku=sku,
            picture_urls=picture_urls

        )
        return [p]
