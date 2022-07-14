from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import OVEN, REFRIGERATOR, WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class TiendaFensa(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR,
            WASHING_MACHINE,
            OVEN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['linea-blanca/refrigerador', REFRIGERATOR],
            ['linea-blanca/lavadoras', WASHING_MACHINE],
            ['linea-blanca/secadoras', WASHING_MACHINE],
            ['linea-blanca/lavadora-secadora', WASHING_MACHINE],
            ['linea-blanca/hornos', OVEN],
            ['linea-blanca/freezer', REFRIGERATOR],
            ['linea-blanca/microondas', OVEN],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)

                url_webpage = 'https://www.tiendafensa.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)

                response = session.get(url_webpage)

                product_container = re.search(r'__STATE__ = {(.+)}',
                                              response.text).groups()[0]

                json_product = json.loads('{' + product_container + '}')
                done = True

                for key, value in json_product.items():
                    if key.startswith('Product:') and 'linkText' in value:
                        product_url = 'https://www.tiendafensa.cl/' + \
                            value['linkText'] + '/p'

                        product_urls.append(product_url)
                        done = False

                if done:
                    if page == 1:
                        logging.warning('Empty category: ' + url_webpage)
                    break
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)

        product_container = re.search(r'__STATE__ = {(.+)}',
                                      res.text).groups()[0]

        product_data = json.loads('{' + product_container + '}')

        base_json_keys = list(product_data.keys())

        if not base_json_keys:
            return []

        base_json_key = base_json_keys[0]
        product_specs = product_data[base_json_key]

        key = product_specs['productId']
        name = product_specs['productName']
        sku = product_specs['productReference']
        description = html_to_markdown(product_specs.get('description', None))

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        normal_price = Decimal(pricing_data['Price'])

        offer_price_key = '{}.teasers.0.effects.parameters.0'.format(
            pricing_key)
        offer_price_json_value = product_data.get(offer_price_key, None)
        if offer_price_json_value:
            offer_price = Decimal(offer_price_json_value['value']) \
                / Decimal(100)
            if offer_price > normal_price:
                offer_price = normal_price
        else:
            offer_price = normal_price

        stock = pricing_data['AvailableQuantity']
        picture_list_key = '{}.items.0'.format(base_json_key)
        picture_list_node = product_data[picture_list_key]
        picture_ids = [x['id'] for x in picture_list_node['images']]

        picture_urls = []
        for picture_id in picture_ids:
            picture_node = product_data[picture_id]
            picture_urls.append(picture_node['imageUrl'].split('?')[0])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
