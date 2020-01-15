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
            ['collections/televisores', 'Television'],
            ['collections/equipos-de-sonido', 'StereoSystem'],
            ['collections/smartphones', 'Cell'],
            ['collections/hornos', 'Oven'],
            ['collections/microondas', 'Oven'],
            ['collections/cocinas', 'Stove'],
            ['collections/anafes', 'Stove'],
            ['collections/lavarropas', 'WashingMachine'],
            ['collections/secarropas', 'WashingMacihne'],
            ['collections/lavasecarropas', 'WashingMachine'],
            ['collections/audifonos', 'Headphones'],
            ['collections/acondicionadores-de-aire', 'AirConditioner']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        base_url = 'https://www.inverfin.com.py/{}?page={}'

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
                product_containers = soup.findAll('div', 'product-item')

                if not product_containers:
                    if page ==1:
                        raise Exception('Empty category: ' + url)
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

        name = soup.find('h1', 'product-meta__title').text.strip()
        sku = soup.find('span', 'product-meta__sku-number').text.strip()
        stock = -1

        if 'LG' not in name.upper().split(' '):
            stock = 0

        price = Decimal(
            soup.find('span', {'id': 'cash-price'}).text.replace('Gs.', '')
                .replace('.', '').strip())

        pictures = soup.findAll('img', 'product-gallery__image')
        picture_urls = []

        for picture in pictures:
            picture_url = 'https:' + picture['data-zoom']
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
