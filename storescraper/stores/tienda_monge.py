from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy

import json


class TiendaMonge(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Television',
            'OpticalDiskPlayer',
            'AirConditioner',
            'Stove',
            'Oven',
            'WashingMachine',
            'Refrigerator',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('125-celulares', 'Cell'),
            ('pantallas', 'Television'),
            ('reproductores-de-video-y-proyectores', 'OpticalDiskPlayer'),
            ('aires-acondicionados', 'AirConditioner'),
            ('cocinas', 'Stove'),
            ('hornos-y-extractores', 'Oven'),
            ('lavadoras-y-secadoras', 'WashingMachine'),
            ('170-refrigeradoras', 'Refrigerator'),
            ('152-minicomponentes', 'StereoSystem'),
            ('163-parlantes', 'StereoSystem'),
            ('sistemas-de-audio-y-accesorios', 'StereoSystem')
        ]

        post_data = {'categoryId': '125',
                     'manufacturerId': '0',
                     'vendorId': '0',
                     'pageNumber': 14,
                     'orderby': 0,
                     'pagesize': '24',
                     'queryString': '',
                     'shouldNotStartFromFirstPage': 'true',
                     'keyword': '',
                     'searchCategoryId': '0',
                     'searchManufacturerId': '0',
                     'searchVendorId': '0',
                     'priceFrom': '',
                     'priceTo': '',
                     'includeSubcategories': 'False',
                     'searchInProductDescriptions': 'False',
                     'advancedSearch': 'False',
                     'isOnSearchPage': 'False'}

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            url = 'https://www.tiendamonge.com/{}'.format(category_path)
            # import ipdb
            # ipdb.set_trace()
            soup = BeautifulSoup(session.get(url).text, 'html5lib')
            print(soup)
            print("nopAjax" in session.get(url).text)
            # store_category = soup.find('div', 'nopAjaxFilters7Spikes')

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        pass
