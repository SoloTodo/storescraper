import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, STORAGE_DRIVE, POWER_SUPPLY, \
    COMPUTER_CASE, RAM, PROCESSOR, MOTHERBOARD, VIDEO_CARD, CPU_COOLER, \
    GAMING_CHAIR, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class CesaPro(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            PROCESSOR,
            MOTHERBOARD,
            VIDEO_CARD,
            CPU_COOLER,
            GAMING_CHAIR,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['569552', CELL],
            ['286086', STORAGE_DRIVE],
            ['572189', POWER_SUPPLY],
            ['286055', COMPUTER_CASE],
            ['286088', RAM],
            ['268198', PROCESSOR],
            ['621424', PROCESSOR],
            ['371788', MOTHERBOARD],
            ['621425', MOTHERBOARD],
            ['286249', VIDEO_CARD],
            ['572184', CPU_COOLER],
            ['640377', GAMING_CHAIR],
            ['667566', MONITOR],
        ]

        session = session_with_proxy(extra_args)
        session.headers[
            'content-type'] = 'application/x-www-form-urlencoded;charset=UTF-8'
        session.headers['x-requested-with'] = 'XMLHttpRequest'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://juan-andres-recabarren-molina.' \
                              'wobiz.cl/ajaxGetFilteredProducts'
                payload = 'filter%5Bpagination%5D%5Bpage%5D={}&filter%5B' \
                          'pagination%5D%5Bcount%5D=30&filter%5Bsort%5D%5' \
                          'Bid%5D=desc&filter%5BcategoryId%5D={}&'.format(
                            page, url_extension)
                print(url_webpage)
                response = session.post(url_webpage, data=payload)
                products_json = response.json()['products']['products']

                if not products_json:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break

                for product in products_json:
                    product_url = product['link']['href']
                    product_urls.append('https://juan-andres-recabarren-'
                                        'molina.wobiz.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers[
            'content-type'] = 'application/x-www-form-urlencoded;charset=UTF-8'
        session.headers['x-requested-with'] = 'XMLHttpRequest'
        product_id = url.split('/')[4]
        product_url = 'https://juan-andres-recabarren-molina.' \
                      'wobiz.cl/ajaxGetProductById'
        payload = 'productId=' + product_id
        response = session.post(product_url, data=payload)
        product_json = response.json()['product']
        name = product_json['name']
        key = str(product_json['id'])
        sku = product_json['sku']
        stock = product_json['total_stock']
        price = Decimal(product_json['right_price'].split('.')[0])
        picture_urls = [product_json['image']['big']]
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

        )
        return [p]
