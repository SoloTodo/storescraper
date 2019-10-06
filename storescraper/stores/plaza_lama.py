from bs4 import BeautifulSoup
from decimal import Decimal
import json

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class PlazaLama(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'OpticalDiskPlayer',
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
            ('4k', 'Television'),
            ('televisores-smart', 'Television'),
            ('televisores-led', 'Television'),
            ('televisores-hd', 'Television'),
            ('sound-bar', 'StereoSystem'),
            ('bocina-portatil', 'StereoSystem'),
            ('audio', 'StereoSystem'),
            ('blu-ray', 'OpticalDiskPlayer'),
            ('tecnologia/celular', 'Cell'),
            ('nevera', 'Refrigerator'),
            ('microondas', 'Oven'),
            ('lavadora', 'WashingMachine'),
            ('secadora', 'WashingMachine'),
            ('lavadora-secadora', 'WashingMachine'),
            ('estufa', 'Stove'),
            ('estufa-de-20', 'Stove'),
            ('aire-acondicionado', 'AirConditioner')
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

                url = 'https://tienda.plazalama.com.do/collections/' \
                      '{}?page={}'.format(category_path, page)

                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                container = soup.find('div', 'grid-uniform')
                items = container.findAll('div', 'grid-item')

                if len(items) == 1 and not items[0].find('a'):
                    break

                for item in items:
                    product_url = 'https://tienda.plazalama.com.do' \
                                  '{}'.format(item.find('a')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')

        script_data = soup.findAll(
            'script', {'type': 'application/ld+json'})
        product_data = None

        for data in script_data:
            json_data = json.loads(data.text, strict=False)
            if json_data['@type'] == 'Product':
                product_data = json_data
                break

        if not product_data:
            raise Exception('No product in {}'.format(url))

        name = product_data['name']
        sku = product_data['sku']

        if product_data['offers']['availability'] == 'InStock':
            stock = -1
        else:
            stock = 0

        price = Decimal(product_data['offers']['price'])

        images_container = soup.find('ul', 'product-photo-thumbs')

        if images_container:
            picture_urls = ['https:{}'.format(image['href'])
                            for image in images_container.findAll('a')]
        else:
            picture_url = soup.find('div', 'product-photo-container')\
                .findAll('img')[-1]['src']
            picture_urls = ['https:{}'.format(picture_url)]

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

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
            'DOP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
