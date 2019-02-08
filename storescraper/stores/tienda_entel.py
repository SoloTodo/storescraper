import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TiendaEntel(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        json_prepago = json.loads(session.get(
            'https://miportal.entel.cl/lista-productos?Nrpp=1000&'
            'format=json-rest').text)

        for record in json_prepago['response']['main'][1]['records']:
            cell_id = record['attributes']['productId'][0]
            cell_url = 'https://miportal.entel.cl/producto/Equipos/' + \
                       cell_id
            product_urls.append(cell_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        return cls._products_for_url(url, extra_args)

    @classmethod
    def _products_for_url(cls, url, extra_args=None, retries=5):
        print(url)
        session = session_with_proxy(extra_args)

        products = []

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        raw_json = soup.find('var', {'id': 'renderData'}).string.strip()

        if not raw_json:
            if retries:
                return cls._products_for_url(url, extra_args,
                                             retries=retries-1)
            else:
                raise Exception('JSON error')

        json_data = json.loads(raw_json)

        description = html_to_markdown(
            str(soup.find('div', 'details-description'))
        )

        for sku in json_data['renderSkusBean']['skus']:
            price_container = sku['skuPrice']
            if not price_container:
                continue

            price = Decimal(price_container).quantize(0)

            if sku['available']:
                stock = -1
            else:
                stock = 0

            sku_id = sku['skuId']

            pictures_container = soup.findAll('div', {'name': sku_id})[2]

            picture_urls = []
            for container in pictures_container.findAll('img'):
                picture_urls.append('https://miportal.entel.cl' +
                                    container['src'].replace(' ', '%20'))

            product = Product(
                sku['skuName'],
                cls.__name__,
                'Cell',
                url,
                url,
                sku_id,
                stock,
                price,
                price,
                'CLP',
                sku=sku_id,
                cell_plan_name='Entel Prepago',
                picture_urls=picture_urls,
                description=description,
            )
            products.append(product)

        return products
