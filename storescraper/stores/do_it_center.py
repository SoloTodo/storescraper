import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class DoItCenter(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'AirConditioner',
            'WashingMachine',
            'StereoSystem',
            'Refrigerator',
            'OpticalDiskPlayer',
            'Oven',
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('linea-blanca/aires-acondicionados', 'AirConditioner'),
            ('linea-blanca/lavadoras', 'WashingMachine'),
            ('linea-blanca/secadoras', 'WashingMachine'),
            ('linea-blanca/refrigeradoras', 'Refrigerator'),
            ('electronica/smart-tv', 'Television'),
            ('electronica/led-tv', 'Television'),
            ('electronica/reproductores-de-video', 'OpticalDiskPlayer'),
            ('electronica/equipos-de-sonido', 'StereoSystem'),
            ('electronica/telefonos-celulares', 'Cell'),
            ('bateria-de-cocina/microondas', 'Oven'),
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.doitcenter.com.pa/collections/{}?page={}' \
                      ''.format(category_path, page)
                print(url)
                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll(
                    'article', 'product-grid-item')

                if not product_containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                for container in product_containers:
                    product_urls.append('https://www.doitcenter.com.pa' +
                                        container.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        sku = soup.find('span', 'product__sku').text.replace(
            'Código ', '').strip()
        brand = soup.find('meta', {'itemprop': 'brand'})['content']
        model = soup.find('h2', 'product__title').text.strip()
        name = '{} {} ({})'.format(brand, model, sku)
        product_id = re.search(r'var productId = (\d+);', data).groups()[0]
        session.headers['authorization'] = \
            'Token token=ca55cd751e3c42fab4ed49b862328a0c'
        store_stock_endpoint = 'https://proxy.doitcenter.com.pa/shopify/api/' \
                               'v1/products/{}/inventories'.format(product_id)

        stock_response = session.get(store_stock_endpoint)

        if stock_response.status_code == 404:
            stock = -1
        else:
            inventories = json.loads(stock_response.text)
            print(inventories)
            stock = 0

            for entry in inventories:
                if entry['inventory_quantity'] is None:
                    continue

                store_stock = int(entry['inventory_quantity'])

                if store_stock < 2:
                    store_stock = 0
                stock += store_stock

        price = Decimal(soup.find('meta', {'itemprop': 'price'})['content'])
        pictures_container = soup.find('div', 'product-images')

        if pictures_container:
            picture_urls = []
            for tag in pictures_container.findAll('a'):
                picture_urls.append('https:' + tag['data-hd-image'])
        else:
            picture_urls = ['https:' + soup.find(
                'meta', {'itemprop': 'image'})['content']]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            product_id,
            stock,
            price,
            price,
            'USD',
            sku=sku,
            picture_urls=picture_urls
        )

        print(p)

        return [p]
