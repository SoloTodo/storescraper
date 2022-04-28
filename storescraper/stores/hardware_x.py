import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class HardwareX(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['65', MONITOR],
            ['64', HEADPHONES],
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
                url_webpage = 'https://www.hardwarex.cl/index.php?route=prod' \
                    'uct/category&path={}&page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_container = soup.find('div', 'main-products')

                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                containers = product_container.findAll('div', 'product-layout')
                for container in containers:
                    product_url = container.find('a', 'product-img')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = url.split('product_id=')[-1]

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        name = json_data['name']
        description = json_data['description']
        # sku = str(json_data['sku'])[50:]
        sku = soup.find('input', {'id': 'product-id'})['value']
        price = Decimal(json_data['offers']['price'])

        max_input = soup.find('li', 'product-stock in-stock')
        if max_input:
            stock = -1
        else:
            stock = 0

        pictures_urls = []
        image_containers = soup.find('div', 'product-image')
        for i in image_containers.findAll('img'):
            pictures_urls.append(i['src'])

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
            picture_urls=pictures_urls,
            description=description
        )
        return [p]
