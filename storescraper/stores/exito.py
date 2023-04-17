import json
from bs4 import BeautifulSoup
from decimal import Decimal
from storescraper.categories import TELEVISION

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, session_with_proxy


class Exito(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 3

    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only gets LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1

        done = False
        while not done:
            if page > 30:
                raise Exception('Page overflow')

            url = 'https://www.exito.com/lg?page={}'.format(page)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            page_state_tag = soup.find('template',
                                       {'data-varname': '__STATE__'})
            page_state = json.loads(page_state_tag.text)

            done = True
            for key, product in page_state.items():
                if 'productId' not in product:
                    continue
                done = False
                product_url = 'https://www.exito.com/{}/p'.format(
                    product['linkText'])
                product_urls.append(product_url)

            if done and page == 1:
                raise Exception('Empty site')

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_data = json.loads(
            soup.find('template', {'data-varname': '__STATE__'}).text)

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        item_key = '{}.items.0'.format(base_json_key)
        key = product_data[item_key]['itemId']
        ean = product_data[item_key]['ean']
        if not check_ean13(ean):
            ean = None

        name = product_specs['productName']
        sku = product_specs['productReference']
        description = product_specs.get('description', None)

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        normal_price = Decimal(str(pricing_data['Price'])) + \
            Decimal(str(pricing_data['Tax']))

        offer_key = '{}.teasers.0.effects.parameters.1'.format(pricing_key)
        if offer_key in product_data:
            offer_data = product_data[offer_key]
            offer_price = (Decimal(str(pricing_data['ListPrice'])) -
                           Decimal(offer_data['value'])).quantize(0, rounding="ROUND_UP")
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
            'COP',
            sku=sku,
            ean=ean,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
