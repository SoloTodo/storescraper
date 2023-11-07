import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import (WEARABLE, KEYBOARD, HEADPHONES,
                                     ALL_IN_ONE, TABLET, CELL, NOTEBOOK,
                                     STEREO_SYSTEM)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class BackOnline(StoreWithUrlExtensions):
    url_extensions = [
        ('WATCH', WEARABLE),
        ('ACCESORIOS', KEYBOARD),
        ('AUDÍFONOS', HEADPHONES),
        ('IMAC', ALL_IN_ONE),
        ('IPAD', TABLET),
        ('IPHONE', CELL),
        ('MACBOOK', NOTEBOOK),
        ('OPEN BOX', NOTEBOOK),
        ('PARLANTES', STEREO_SYSTEM),
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []

        for collection_label, collection_url in extra_args['collection_urls']:
            if url_extension not in collection_label:
                continue

            page = 1
            while True:
                if page >= 5:
                    raise Exception('Page overflow: ' + url_extension)

                url_webpage = '{}?page={}'.format(collection_url, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                link_containers = soup.findAll('li', 'grid__item')

                if not link_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for link_container in link_containers:
                    product_url = ('https://backonline.cl' +
                                   link_container.find('a')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        json_tag = soup.findAll('script', {'type': 'application/ld+json'})
        json_data = json.loads(json_tag[1].text)

        if 'NUEVO' in json_data['brand']['name'].upper():
            condition = 'https://schema.org/NewCondition'
        elif 'OPEN BOX' in json_data['brand']['name'].upper():
            condition = 'https://schema.org/OpenBoxCondition'
        else:
            condition = 'https://schema.org/RefurbishedCondition'

        variations_tags = soup.findAll('script', {'type': 'application/json'})
        products = []

        if len(variations_tags) == 1:
            name = json_data['name'].strip()
            sku = json_data['sku']
            picture_urls = json_data['image']

            offer = json_data['offers'][0]
            key = re.search(r'variant=(\d+)$', offer['url']).groups()[0]
            stock = -1 if (offer['availability'] ==
                           'http://schema.org/InStock') else 0
            price = Decimal(offer['price']).quantize(0)

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
                part_number=sku,
                picture_urls=picture_urls,
                condition=condition
            )
            products.append(p)
        else:
            variations = json.loads(variations_tags[2].text)
            for variation in variations:
                name = variation['name']
                key = str(variation['id'])
                stock = -1 if variation['available'] else 0
                price = Decimal(variation['price'] / 100).quantize(0)
                sku = variation['sku']

                if not sku:
                    continue

                if variation['featured_image']:
                    picture_urls = ['https:' +
                                    variation['featured_image']['src']]
                else:
                    picture_urls = None

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
                    part_number=sku,
                    picture_urls=picture_urls,
                    condition=condition
                )
                products.append(p)

        return products

    @classmethod
    def preflight(cls, extra_args=None):
        session = session_with_proxy(extra_args)

        response = session.get('https://backonline.cl/collections')
        soup = BeautifulSoup(response.text, 'html.parser')

        collection_cells = soup.findAll('li', 'collection-list__item')
        collection_urls = []

        for collection_cell in collection_cells:
            collection_link = collection_cell.find('a')

            if 'href' not in collection_link.attrs:
                continue

            cell_label = collection_cell.find('h3').text.upper()
            collection_url = 'https://backonline.cl' + collection_link['href']
            collection_urls.append((cell_label, collection_url))

        return {
            'collection_urls': collection_urls
        }
