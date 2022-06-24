from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, CELL, HEADPHONES, MOUSE, \
    NOTEBOOK, STEREO_SYSTEM, TABLET, WEARABLE, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy, \
    html_to_markdown


class Aufbau(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            TABLET,
            ALL_IN_ONE,
            NOTEBOOK,
            WEARABLE,
            HEADPHONES,
            STEREO_SYSTEM,
            MOUSE,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['aufbauIphone', CELL],
            ['aufbauIpad', TABLET],
            ['aufbauiMac', ALL_IN_ONE],
            ['aufbauMacBookPro', NOTEBOOK],
            ['MacBookAir', NOTEBOOK],
            ['aufbauWatch', WEARABLE],
            ['aufbauAirPods', HEADPHONES],
            ['aufbauAudioAudifonos', HEADPHONES],
            ['aufbauAudioBeats', HEADPHONES],
            ['aufbauAudioParlantes', STEREO_SYSTEM],
            ['aufbauAccesoriosMouseTeclados', MOUSE],
            ['aufbauStudioDisplay', MONITOR],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://api.cxl8rgz-articulos1-p1-public.mod' \
                'el-t.cc.commerce.ondemand.com/rest/v2/reifst' \
                'oreb2cstore/products/search?query=%3Arelevan' \
                'ce%3AallCategories%3A{}'.format(url_extension)
            data = session.get(url_webpage).text

            product_containers = json.loads(data)['products']
            if len(product_containers) == 0:
                logging.warning('Empty category: ' + url_extension)
                continue
            for container in product_containers:
                url = container['url'].split('reifstore-encoding')[0]
                product_urls.append(
                    'https://www.aufbau.cl' +
                    url + container['code'].replace('/', '--'))
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        code = url.split('/p/')[-1].replace('--', '/')
        session = session_with_proxy(extra_args)
        data = session.get(
            'https://api.cxl8rgz-articulos1-p1-public.model-t.cc.commerce.'
            'ondemand.com/rest/v2/reifstoreb2cstore/products/reifstore-enc'
            'oding?productCode={}'.format(code)
        ).text

        product_info = json.loads(data)

        base_name = product_info['name']
        description = html_to_markdown(product_info['description'])
        picture_urls = []
        for i in product_info['images']:
            if i['format'] == 'product':
                picture_urls.append('https://api.cxl8rgz-articulos1-p1-public'
                                    '.model-t.cc.commerce.ondemand.com' +
                                    i['url'])

        products = []
        if 'variantOptions' in product_info:
            for variant in product_info['variantOptions']:
                code = variant['code']
                variant_url = 'https://www.aufbau.cl' + \
                    variant['url'].replace('%2F', '--')
                price = Decimal(variant['priceData']['value'])
                stock = variant['stock']['stockLevel']

                variation_name = base_name + ' -'
                for v in variant['variantOptionQualifiers']:
                    variation_name += ' ' + v['value']

                p = Product(
                    variation_name,
                    cls.__name__,
                    category,
                    variant_url,
                    url,
                    code,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=code,
                    part_number=code,
                    picture_urls=picture_urls,
                    description=description
                )
                products.append(p)
        else:
            code = product_info['code']
            price = Decimal(remove_words(
                product_info['price']['formattedValue']))
            stock_json = product_info['stock']
            if 'stockLevel' in stock_json:
                stock = stock_json['stockLevel']
            else:
                if stock_json['stockLevelStatus'] == 'inStock':
                    stock = -1
                else:
                    stock = 0

            p = Product(
                base_name,
                cls.__name__,
                category,
                url,
                url,
                code,
                stock,
                price,
                price,
                'CLP',
                sku=code,
                part_number=code,
                picture_urls=picture_urls,
                description=description
            )
            products.append(p)

        return products
