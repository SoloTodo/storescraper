import json
import logging
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
                        logging.warning('Empty category: ' + url)
                    break

                for container in product_containers:
                    if container.find('span', 'product-grid-item__vendor')\
                            .text.strip().upper() != 'LG':
                        continue
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
        stock = -1

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

        return [p]
