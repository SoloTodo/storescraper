import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Siman(Store):
    country_url = ''
    currency_iso = ''

    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        product_urls = []

        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            done = False
            while not done:
                if page > 30:
                    raise Exception('Page overflow')

                url_webpage = 'https://{}.siman.com/lg?page={}'.format(
                    cls.country_url, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                page_state_tag = soup.find('template',
                                           {'data-varname': '__STATE__'})
                page_state = json.loads(page_state_tag.text)
                done = True

                for key, product in page_state.items():
                    if 'productId' not in product:
                        continue
                    done = False
                    # if product['brand'].upper() != 'LG':
                    #     continue
                    product_url = 'https://{}.siman.com/{}/p'.format(
                        cls.country_url, product['linkText'])
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
        soup = BeautifulSoup(response.text, 'html5lib')

        product_data = json.loads(
            soup.find('template', {'data-varname': '__STATE__'}).text)

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        if product_specs['brand'] != 'LG':
            return []

        name = product_specs['productName']
        sku = product_specs['productReference']
        description = product_specs.get('description', None)

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(str(pricing_data['Price']))
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
            sku,
            stock,
            price,
            price,
            cls.currency_iso,
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
