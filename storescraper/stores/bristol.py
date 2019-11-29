from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Bristol(Store):
    base_url = 'https://www.lg.com'
    country_code = 'cl'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Projector',
            'Cell',
            'Refrigerator',
            'Oven',
            'Stove',
            'WashingMachine',
            'AirConditioner'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['televisores-hd-c166', 'Television'],
            ['televisores-fhd-c167', 'Television'],
            ['televisores-uhd-4k-c168', 'Television'],
            ['audio-c48', 'StereoSystem'],
            ['proyectores-c169', 'Projector'],
            ['celulares-f3', 'Cell'],
            ['refrigeracion-c7', 'Refrigerator'],
            ['hornos-electricos-c21', 'Oven'],
            ['microondas-c23', 'Oven'],
            ['cocinas-c20', 'Stove'],
            ['lavado-c9', 'WashingMachine'],
            ['split-ecologico-c13', 'AirConditioner']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        base_url = 'https://bristol.com.py/{}.{}'

        for c in category_paths:
            category_path, local_category = c

            if category != local_category:
                continue

            page = 1

            while True:
                url = base_url.format(category_path, page)

                if page >= 15:
                    raise Exception('Page overflow' + url)

                print(url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('div', 'product-item-box')

                if not product_containers:
                    break

                for product in product_containers:
                    product_url = 'https://bristol.com.py/{}'.format(
                        product.find('a')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'product-title').text.strip()
        sku = soup.find('div', 'product-desc').text.split('/')[0].replace('Cod:', '').strip()
        stock = -1

        if 'LG' not in name.upper().split(' '):
            stock = 0

        price = Decimal(
            soup.find('div', 'product-price').find('span')
                .text.replace('Gs.', '').replace('.', '').strip())

        pictures = soup.find('ul', {'id': 'imageGallery'}).findAll('li')
        picture_urls = []

        for picture in pictures:
            picture_url = picture.find('img')['src'].replace(' ', '%20')
            picture_urls.append(picture_url)

        return [Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'PYG',
            sku=sku,
            picture_urls=picture_urls
        )]
