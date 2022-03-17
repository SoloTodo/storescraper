from decimal import Decimal
import json
import logging
import re

from bs4 import BeautifulSoup
from storescraper.categories import AIR_CONDITIONER, OVEN, \
    REFRIGERATOR, SPACE_HEATER, TELEVISION, WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class OutletMedina(Store):
    @classmethod
    def categories(cls):
        return {
            REFRIGERATOR,
            WASHING_MACHINE,
            OVEN,
            SPACE_HEATER,
            TELEVISION,
            AIR_CONDITIONER,
        }

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['3-refrigeradores', REFRIGERATOR],
            ['12-freezer', REFRIGERATOR],
            ['25-frigobar', REFRIGERATOR],
            ['14-lavadoras', WASHING_MACHINE],
            ['16-secadoras', WASHING_MACHINE],
            ['53-centrifugas', WASHING_MACHINE],
            ['59-microondas-y-hornos-electricos', OVEN],
            ['21-estufas', SPACE_HEATER],
            ['63-termoventiladores', SPACE_HEATER],
            ['78-televisores', TELEVISION],
            ['85-aire-acondicionado', AIR_CONDITIONER],
        ]

        session = session_with_proxy(extra_args)
        session.headers['Accept'] = 'application/json, ' \
                                    'text/javascript, */*; q=0.01'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://outletmedina.cl/{}' \
                              '?page={}'.format(url_extension, page)
                data_json = json.loads(session.get(url_webpage).text)
                soup = BeautifulSoup(
                    data_json['rendered_products'], 'html.parser')
                product_containers = soup.findAll(
                    'div', 'js-product-miniature-wrapper')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a', 'thumbnail')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        product_json = json.loads(
            soup.find('div', {'id': 'product-details'})['data-product'])

        name = product_json['name']
        key = str(product_json['id_product'])
        price = Decimal(product_json['price'])
        stock = product_json['quantity']
        description = html_to_markdown(product_json['description'])

        image_list = soup.find(
            'div', {'id': 'product-images-large'}).findAll('img')
        image_urls = []
        for image in image_list:
            image_urls.append(image['data-image-large-src'])

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
            sku=key,
            description=description,
            picture_urls=image_urls,
            condition='https://schema.org/RefurbishedCondition'
        )

        return [p]
