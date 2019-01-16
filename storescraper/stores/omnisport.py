from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Omnisport(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'AirConditioner',
            'WashingMachine',
            'OpticalDiskPlayer',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('video/android-tv', 'Television'),
            ('video/pantallas-led', 'Television'),
            ('video/oled-tv', 'Television'),
            ('video/smart-tv', 'Television'),
            ('video/4k-tv', 'Television'),
            ('audio/mini-parlantes', 'StereoSystem'),
            ('audio/equipos-de-sonido', 'StereoSystem'),
            ('audio/sistema-de-teatro', 'StereoSystem'),
            ('electronica/celulares', 'Cell'),
            ('electrodomesticos/refrigeradores', 'Refrigerator'),
            ('electrodomesticos/hornos', 'Oven'),
            ('electrodomesticos/microondas', 'Oven'),
            ('electrodomesticos/aires-acondicionados/productos',
             'AirConditioner'),
            ('electrodomesticos/lavadoras', 'WashingMachine'),
            ('electrodomesticos/secadoras', 'WashingMachine'),
            ('video/dvd', 'OpticalDiskPlayer'),
            ('video/blu-ray', 'OpticalDiskPlayer'),
            ('electrodomesticos/cocinas', 'Stove')
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

                url = 'https://www.omnisport.com/catalogo/{}?page={}'\
                    .format(category_path, page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                containers = soup.findAll('div', 'catalog-product')

                if not containers:
                    done = True

                for container in containers:
                    product_url = 'https://www.omnisport.com{}'\
                        .format(container.find('a')['href'])

                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        text_info = soup.find('div', 'main-product-info-inner').find('h3')

        sku = text_info.find('span').contents[3].strip()
        model = text_info.find('span').contents[1].replace('|', '').strip()
        name = '{} ({})'.format(text_info.find('strong').text.strip(), model)

        price_containers = soup.findAll('p', 'product-price')

        if len(price_containers) == 1:
            price = price_containers[0].find('span').text
            offer_price = price
        elif len(price_containers) == 2:
            price = price_containers[1].find('span').text
            offer_price = price
        else:
            price = price_containers[1].find('span').text
            offer_price = price_containers[2].find('span').text

        price = cls.fix_price(price)
        offer_price = cls.fix_price(offer_price)

        picture_urls = []
        pictures = soup.find('div', 'gallery-carrousel').findAll('div')

        for picture in pictures:
            if picture.find('a'):
                picture_urls.append('https://www.omnisport.com{}'
                                    .format(picture.find('a')['href']))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            offer_price,
            'USD',
            sku=sku,
            picture_urls=picture_urls
        )

        return [p]

    @staticmethod
    def fix_price(price):
        split_price = price.split('.')
        fixed_price = split_price[0]+'.'+split_price[1]
        return Decimal(fixed_price.replace('$', '').replace(',', ''))
