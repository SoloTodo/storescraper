import json
import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper.categories import TELEVISION, STEREO_SYSTEM, CELL, \
    REFRIGERATOR, OVEN, WASHING_MACHINE, STOVE, CELL_ACCESORY, HEADPHONES, \
    MONITOR, AIR_CONDITIONER, WEARABLE, VACUUM_CLEANER


class Jetstereo(Store):
    base_url = 'https://www.jetstereo.com'

    @classmethod
    def categories(cls):
        return [
            STEREO_SYSTEM,
            TELEVISION,
            CELL,
            REFRIGERATOR,
            STOVE,
            OVEN,
            WASHING_MACHINE,
            CELL_ACCESORY,
            HEADPHONES,
            MONITOR,
            AIR_CONDITIONER,
            WEARABLE,
            VACUUM_CLEANER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_path = {
            STEREO_SYSTEM: ['48', '212'],
            TELEVISION: ['41'],
            CELL: ['26'],
            REFRIGERATOR: ['74', '159', '195', '160', '161'],
            STOVE: ['75', '163', '164'],
            OVEN: ['76'],
            WASHING_MACHINE: ['77', '157', '78', '249', '158', '156'],
            CELL_ACCESORY: ['63'],
            HEADPHONES: ['132'],
            MONITOR: ['91'],
            AIR_CONDITIONER: ['79'],
            WEARABLE: ['89'],
            VACUUM_CLEANER: ['152'],
        }
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 20:
                raise Exception('Page overflow')
            url = 'https://api.jetstereo.com/manufacturers/2/products?' \
                  'per-page=20&page={}'.format(page)
            print(url)
            response = session.get(url)
            product_containers = json.loads(response.text)
            if page > product_containers['_meta']['pageCount']:
                break
            product_containers = product_containers['content']

            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url)
                break

            for container in product_containers:
                if container['mainCategory']['id'] not in \
                        category_path[category]:
                    continue
                product_url = 'https://www.jetstereo.com/product/' + \
                              container['url'].split('.com/')[-1]
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_json = json.loads(
            soup.find('script', {'id': '__NEXT_DATA__'}).text)['props'][
            'pageProps']['product']
        name = product_json['name']
        sku = str(product_json['id'])
        part_number = product_json['sku']

        if product_json['saleStatus'] == 'AVAILABLE':
            stock = -1
        else:
            stock = 0
        price = Decimal(product_json['price']['sale']).quantize(
            Decimal('.01'))
        picture_urls = [urllib.parse.quote(picture_url, safe='://') for
                        picture_url in
                        product_json['allImages']['full']]

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            part_number=part_number
        )

        return [p]
