from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup

from storescraper.categories import CELL, STEREO_SYSTEM, NOTEBOOK, VIDEO_CARD
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class MyaOutlet(StoreWithUrlExtensions):
    url_extensions = [
        ['tecnologia/celulares', CELL],
        ['parlantes', STEREO_SYSTEM],
        ['tecnologia/macbook', NOTEBOOK],
        ['tecnologia/notebook', NOTEBOOK],
        ['tecnologia/notebook-gamer', NOTEBOOK],
        ['computacion/componentes', VIDEO_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('Page overflow: ' + url_extension)
            url_webpage = ('https://myaoutlet.cl/categoria-producto/'
                           'tecnologia/{}/page/{}/').format(
                            url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            products_wrapper = soup.find('ul', 'products')

            if not products_wrapper:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break

            product_containers = products_wrapper.findAll('li')

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[1].text)

        name = json_data['name']
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]

        if json_data['offers'][0]['availability'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        supplied_part_number = json_data['sku']
        if isinstance(supplied_part_number, str):
            part_number = supplied_part_number
        else:
            part_number = None

        if not part_number and category == NOTEBOOK and stock != 0:
            raise Exception('Available notebook without MPN')

        price = Decimal(json_data['offers'][0]['price'])
        picture_urls = [json_data['image']]

        description = json_data['description']

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
            sku=part_number,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number,
            condition='https://schema.org/RefurbishedCondition'
        )
        return [p]
