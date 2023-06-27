import json

from bs4 import BeautifulSoup
from decimal import Decimal
from storescraper.categories import MONITOR, NOTEBOOK

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, session_with_proxy, remove_words


class AcerStore(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['notebook-gamer', NOTEBOOK],
            ['notebook', NOTEBOOK],
            ['monitores/monitores-pc', MONITOR],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_id, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False
            while not done:
                if page >= 10:
                    raise Exception('Page overflow')

                category_url = 'https://www.acerstore.cl/{}/' \
                               '?page={}'.format(category_id, page)
                print(category_url)

                data = session.get(category_url).text
                soup = BeautifulSoup(data, 'html.parser')
                page_state_tag = soup.find('template',
                                           {'data-varname': '__STATE__'})
                page_state = json.loads(page_state_tag.text)

                done = True
                for key, product in page_state.items():
                    if 'productId' not in product:
                        continue
                    done = False
                    product_url = 'https://www.acerstore.cl/{}/p'.format(
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
        soup = BeautifulSoup(response.text, 'html5lib')

        product_data = json.loads(
            soup.find('template', {'data-varname': '__STATE__'}).text)

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        key = product_specs['productId']
        name = product_specs['productName']
        sku = product_specs['productReference']
        description = product_specs.get('description', None)

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(str(pricing_data['Price']))

        if not price:
            pricing_key = '{}.specificationGroups.2.specifications.0'.format(
                base_json_key)
            price = Decimal(remove_words(product_data[pricing_key]['name']))

        stock = pricing_data['AvailableQuantity']
        picture_list_key = '{}.items.0'.format(base_json_key)
        picture_list_node = product_data[picture_list_key]
        picture_ids = [x['id'] for x in picture_list_node['images']]

        picture_urls = []
        for picture_id in picture_ids:
            picture_node = product_data[picture_id]
            picture_urls.append(picture_node['imageUrl'].split('?')[0])

        item_key = '{}.items.0'.format(base_json_key)
        part_number = product_data[item_key]['name']

        ean = None
        for property in product_specs['properties']:
            if product_data[property['id']]['name'] == 'EAN':
                ean = product_data[property['id']]['values']['json'][0]
                if check_ean13(ean):
                    break
                else:
                    ean = None

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
            part_number=part_number,
            ean=ean,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
