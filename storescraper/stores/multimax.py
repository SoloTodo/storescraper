from bs4 import BeautifulSoup
from decimal import Decimal
import json

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown

from storescraper.utils import check_ean13


class Multimax(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'Stove',
            'AirConditioner'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('led-tv', 'Television'),
            ('smart-tv', 'Television'),
            ('4k-tv', 'Television'),
            ('android', 'Cell'),
            ('equipos-de-sonido', 'StereoSystem'),
            ('barras-de-sonido', 'StereoSystem'),
            ('bocinas-portatiles', 'StereoSystem'),
            ('9-000-btu', 'AirConditioner'),
            ('12-000-btu', 'AirConditioner'),
            ('18-000-btu', 'AirConditioner'),
            ('24-000-btu', 'AirConditioner'),
            ('inverter', 'AirConditioner'),
            ('estufas', 'Stove'),
            ('lavadoras', 'WashingMachine'),
            ('secadoras', 'WashingMachine'),
            ('centro-de-lavado', 'WashingMachine'),
            ('refrigeradoras', 'Refrigerator'),
            # ('congeladores', 'Refrigerator'),
            # ('microondas', 'Oven'),
            ('hornos', 'Oven')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://shopmultimax.com/collections/{}?page={}'\
                    .format(category_path, page)

                print(url)

                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                container = soup.find('div', 'productgrid--items')

                items = container.findAll('div', 'productitem')
                if items:
                    for item in items:
                        product_url = 'https://shopmultimax.com{}'\
                            .format(item.find('a')['href'])
                        product_urls.append(product_url)
                else:
                    if page == 1:
                        raise Exception('No products for category {}'
                                        .format(category))
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        products = []

        products_data = soup.find('script',
                                  {'data-section-type': 'static-product'})

        json_data = json.loads(products_data.text)['product']

        description = html_to_markdown(json_data['description'])

        images = json_data['images']
        picture_urls = ['https:{}'.format(image.split('?')[0])
                        for image in images]

        for variant in json_data['variants']:
            name = variant['name']
            sku = variant['sku']
            barcode = variant['barcode']

            if len(barcode) == 12:
                barcode = '0' + barcode

            if not check_ean13(barcode):
                barcode = None

            stock = variant['inventory_quantity']
            price = Decimal(variant['price'])/Decimal(100)

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                'USD',
                sku=sku,
                ean=barcode,
                description=description,
                picture_urls=picture_urls
            ))

        return products
