from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Inverfin(Store):
    base_url = 'https://www.lg.com'
    country_code = 'cl'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'OpticalDiskPlayer',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'Stove',
            'WashingMachine',
            'Headphones',
            'AirConditioner'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['tv-y-audio/televisores', 'Television'],
            ['tv-y-audio/reproductores', 'OpticalDiskPlayer'],
            ['tv-y-audio/equipos-de-sonido', 'StereoSystem'],
            ['tv-y-audio/parlante-portatil', 'StereoSystem'],
            ['tecnologia/celulares', 'Cell'],
            ['hogar/hornos', 'Oven'],
            ['hogar/microondas', 'Oven'],
            ['hogar/cocinas', 'Stove'],
            ['hogar/anafes', 'Stove'],
            ['hogar/lavarropas', 'WashingMachine'],
            ['hogar/secarropas', 'WashingMacihne'],
            ['hogar/lavasecarropas', 'WashingMachine'],
            ['tv-y-audio/auriculares', 'Headphones'],
            ['hogar/aire-acondicionado', 'AirConditioner']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        base_url = 'https://www.inverfin.com.py/{}?pagina={}'

        for c in category_paths:
            category_path, local_category = c

            if category != local_category:
                continue

            page = 1

            while True:
                url = base_url.format(category_path, page)

                if page >= 15:
                    raise Exception('Page overflow' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('div', 'item')

                if not product_containers:
                    break

                for product in product_containers:
                    product_url = 'https://inverfin.com.py{}'.format(
                        product.find('a')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h2', 'product-name').text.strip()
        sku = soup.find('h2', 'product-name').find('small').text.strip()
        name = name.replace(sku, '').strip()
        stock = -1

        if 'LG' not in name.upper().split(' '):
            stock = 0

        price = Decimal(
            soup.find('span', 'main-price').find('span', 'deadline-price')
                .text.replace('Gs.', '').replace('.', '').strip())*6

        pictures = soup.findAll('img', 'zoomable-img')
        picture_urls = []

        for picture in pictures:
            picture_url = 'https://inverfin.com.py{}'\
                .format(picture['data-zoom-image'])
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
