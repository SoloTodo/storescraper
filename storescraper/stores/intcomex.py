import ssl
import requests

from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import datetime
from hashlib import sha256
from urllib3 import poolmanager

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        try:
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        except Exception:
            pass
        self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_version=ssl.PROTOCOL_TLS,
                ssl_context=ctx)


class Intcomex(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('cpt.notebook', 'Notebook')
        ]

        discovered_urls = []

        for category_path, local_category in category_paths:
            if category != local_category:
                continue

            discovered_urls.append(
                'https://store.intcomex.com/es-XCL/ProductsAjax/'
                'ByCategory/{}?rpp=600&X-Requested-With=XMLHttpRequest'
                ''.format(category_path))

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        cells = soup.findAll('div', 'productListItemGrid')
        skus_dict = {}
        for cell in cells:
            sku = cell.find('span', 'js-skuProduct').text.strip()
            name = cell.find('div', 'product-name').text.strip()
            url_id = cell['data-recno']
            skus_dict[sku] = {'name': name, 'url_id': url_id}

        skus = list(skus_dict.keys())

        session = session_with_proxy(extra_args)
        step_size = 100
        currencies_dict = {
            'us': 'USD'
        }

        scraper_mode = extra_args['scraper_mode']
        products = []

        for i in range((len(skus) // step_size) + 1):
            skus_slice = skus[step_size * i:step_size * (i + 1)]
            sku_query = ','.join(skus_slice)

            res = session.get(
                'https://intcomex-{}.apigee.net/v1/getproducts?skusList={}'
                ''.format(scraper_mode, sku_query),
                headers={'Authorization': extra_args['authorization_header']})

            for sku_entry in res.json():
                name = skus_dict[sku_entry['Sku']]['name']
                product_url = 'https://store.intcomex.com/es-XCL/Product/' \
                              'Detail/' + skus_dict[sku_entry['Sku']]['url_id']
                stock = extra_args['stock_data'].get(sku_entry['Sku'], 0)
                description = sku_entry['Description']
                currency = currencies_dict[sku_entry['Price']['CurrencyId']]
                price = Decimal(str(sku_entry['Price']['UnitPrice']))
                products.append(Product(
                    name,
                    cls.__name__,
                    category,
                    product_url,
                    url,
                    sku_entry['Sku'],
                    stock,
                    price,
                    price,
                    currency,
                    part_number=sku_entry['Mpn'],
                    description=description
                ))

        return products

    @classmethod
    def preflight(cls, extra_args=None):
        api_key = extra_args['api_key']
        access_key = extra_args['access_key']
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
        decoded_signature = ','.join([api_key, access_key, timestamp])
        signature = sha256(decoded_signature.encode('ascii')).hexdigest()

        auth = 'Bearer apiKey={}&utcTimeStamp={}&signature={}'.format(
            api_key, timestamp, signature
        )
        session = session_with_proxy(extra_args)
        scraper_mode = extra_args['scraper_mode']

        res = session.get('https://intcomex-{}.apigee.net/v1/getinventory'
                          ''.format(scraper_mode),
                          headers={'Authorization': auth})

        stock_data = {x['Sku']: x['InStock'] for x in res.json()}

        return {
            'authorization_header': auth,
            'stock_data': stock_data
        }
