import json
import re
import urllib.parse
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TravelTienda(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        product_urls = []

        session = session_with_proxy(extra_args)
        url_webpage = 'https://tienda.travel.cl/ccstore/v1/assembler/pages/' \
                      'Default/osf/catalog?Ntt=samsung&Nrpp=1000&' \
                      'Nr=AND%28sku.availabilityStatus%3AINSTOCK%29'
        print(url_webpage)
        response = session.get(url_webpage)
        json_data = response.json()
        for product_entry in json_data['results']['records']:
            product_path = product_entry['attributes']['product.route'][0]
            product_urls.append(
                'https://tienda.travel.cl' + product_path)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'data-name': 'occ-structured-data'})

        if not script_tag:
            print('FOO')
            if extra_args:
                retries = extra_args.get('retries', 5)
                if retries > 0:
                    retries -= 1
                    extra_args['retries'] = retries
                    return cls.products_for_url(url, category, extra_args)
                else:
                    raise Exception('Empty product page: ' + url)
            else:
                extra_args = {'retries': 5}
                return cls.products_for_url(url, category, extra_args)

        product_json = json.loads(script_tag.text)[0]
        data = soup.find('body').find('script').text

        data_clean = urllib.parse.unquote(
            re.search(r'window.state = JSON.parse\(decodeURI\((.+)\)\)',
                      data).groups()[0])
        json_container = list(
            json.loads(data_clean[1:-1])['catalogRepository'][
                'products'].values())[0]
        name = product_json['name']
        sku = product_json['sku']
        stock = -1
        normal_price = Decimal(product_json['offers']['price'])
        offer_price = Decimal(
            json_container['listPrices']['tiendaBancoDeChile'])
        picture_urls = ['https://tienda.travel.cl' +
                        picture.replace(' ', '%20') for picture in
                        json_container['fullImageURLs']]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )

        return [p]
