import json
import urllib
from collections import OrderedDict
from decimal import Decimal

import re

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class FalabellaArgentina(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_paths = [
            ['cat140020/Heladeras', 'Refrigerator'],
            ['cat10044/Aires-acondicionados', 'AirConditioner'],
            ['cat10158/Calefones', 'WaterHeater'],
            ['cat10076/Lavarropas', 'WashingMachine'],
            ['cat10078/Secarropas', 'WashingMachine'],
            ['cat140022/Lavasecarropas', 'WashingMachine'],
            ['cat10148/Cocinas', 'Stove'],
            ['cat10152/Anafes', 'Stove'],
        ]

        session = session_with_proxy(extra_args)
        session.headers.update({
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en,en-US;q=0.8,es;q=0.6',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'DNT': '1',
            'Host': 'www.falabella.com.ar',
            'Referer': 'https://www.falabella.com.ar/falabella-ar/',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 '
                          'Safari/537.36'
        })
        session.get('https://www.falabella.com.ar/falabella-ar/')
        session.get('https://www.falabella.com.ar/falabella-ar/'
                    'includes/ajaxFirstNameAndCartQuantity.jsp')
        discovered_urls = []

        for url_path, local_category in url_paths:
            if local_category != category:
                continue

            sorters = [
                None,  # No sorting
                1,  # Precio menor a mayor
                2,  # Precio mayor a menor
                3,  # Marca
                4,  # Destacados
                5,  # Recomendados
                6,  # Mejor evaluados
                7,  # Nuevos productos
            ]

            # Falabella tends to... fail... so try different requests using
            # the different available sorters... twice... just in case.
            category_product_urls = None

            for i in range(2 * len(sorters)):
                try:
                    category_product_urls = cls._get_category_product_urls(
                        session,
                        url_path,
                        sorters[i % len(sorters)]
                    )
                    break
                except Exception:
                    continue

            if not category_product_urls:
                raise Exception('Category error: ' + url_path)

            discovered_urls.extend(category_product_urls)

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        content = session.get(url).text.replace('&#10;', '')

        soup = BeautifulSoup(content, 'html.parser')

        panels = ['fb-product-information__product-information-tab',
                  'fb-product-information__specification']

        description = ''

        for panel in panels:
            description += html_to_markdown(str(soup.find('div', panel))) + \
                           '\n\n'

        raw_json_data = re.search('var fbra_browseMainProductConfig = (.+);\r',
                                  content)

        if not raw_json_data:
            return []

        product_data = json.loads(raw_json_data.groups()[0])

        brand = product_data['state']['product']['brand']
        model = product_data['state']['product']['displayName']
        full_name = '{} {}'.format(brand, model)

        global_id = product_data['state']['product']['id']
        media_asset_url = product_data['endPoints']['mediaAssetUrl']['path']

        pictures_resource_url = 'http://falabella.scene7.com/is/image/' \
                                'FalabellaAR/{}?req=set,json'.format(global_id)
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      session.get(pictures_resource_url).text).groups()[0])

        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https:{}{}?scl=1.0'.format(
                media_asset_url, picture_entry['i']['n'])
            picture_urls.append(picture_url)

        products = []
        for model in product_data['state']['product']['skus']:
            if 'stockAvailable' not in model:
                continue

            sku = model['skuId']

            prices = {e['type']: e for e in model['price']}

            lookup_field = 'originalPrice'
            if lookup_field not in prices[3]:
                lookup_field = 'formattedLowestPrice'

            normal_price = Decimal(remove_words(prices[3][lookup_field]))

            if 1 in prices:
                lookup_field = 'originalPrice'
                if lookup_field not in prices[1]:
                    lookup_field = 'formattedLowestPrice'
                offer_price = Decimal(
                    remove_words(prices[1][lookup_field]))
            else:
                offer_price = normal_price

            stock = model['stockAvailable']

            p = Product(
                full_name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                normal_price,
                offer_price,
                'ARS',
                sku=sku,
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)

        return products

    @classmethod
    def _get_category_product_urls(cls, session, url_path, sorter):
        discovered_urls = []
        query_args = OrderedDict([
            ('currentPage', 1),
            # ('sortBy', sorter),
            ('navState', "/category/{}?sortBy={}".format(url_path, sorter))])

        if not sorter:
            query_args['navState'] = "/category/{}".format(url_path)

        page = 1

        while True:
            if page > 30:
                raise Exception('Page overflow: ' + url_path)

            res = None

            error_count = 0
            while res is None or 'errors' in res:
                error_count += 1
                if error_count > 10:
                    raise Exception('Error threshold exceeded: ' + url_path)
                query_args['currentPage'] = page
                pag_url = 'https://www.falabella.com.ar/rest/model/' \
                          'falabella/rest/browse/BrowseActor/' \
                          'get-product-record-list?{}'.format(
                            urllib.parse.quote(json.dumps(
                                query_args, separators=(',', ':')), safe=''))

                print(pag_url)

                res = json.loads(
                    session.get(pag_url).content.decode('utf-8'))

            if not res['state']['resultList'] and page == 1:
                raise Exception('Empty category path: ' + url_path)

            for product_entry in res['state']['resultList']:
                product_id = product_entry['productId'].strip()
                product_url = \
                    'https://www.falabella.com.ar/falabella-ar/product/{}/' \
                    ''.format(product_id)
                discovered_urls.append(product_url)

            if res['state']['pagesTotal'] == page:
                break

            page += 1

        return discovered_urls
