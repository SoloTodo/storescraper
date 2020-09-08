from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Tupi(Store):
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
            # Televisores
            ['189', 'Television'],
            # Audio
            ['192', 'StereoSystem'],
            # Celulares_y_Tablets
            ['155', 'Cell'],
            # Heladeras
            ['158', 'Refrigerator'],
            # Heladeras y freezers
            ['13', 'Refrigerator'],
            # Hornos
            ['168', 'Oven'],
            # Microondas
            ['172', 'Oven'],
            # Lavado
            ['33', 'WashingMachine'],
            # Climatización
            ['12', 'AirConditioner']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        base_url = 'https://www.tupi.com.py/familias_paginacion/{}/{}/'

        for c in category_paths:
            category_path, local_category = c

            if category != local_category:
                continue

            page = 1

            while True:
                url = base_url.format(category_path, page)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                print(url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    break

                for product in product_containers:
                    product_link = product.findAll('a')[1]
                    if 'lg' in product_link.text.lower():
                        product_urls.append(product_link['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()
        sku = soup.find(
            'meta', {'property': 'product:retailer_item_id'})['content']

        if not soup.find('input', {'id': 'the-cantidad-selector'}):
            return []

        stock = soup.find('input', {'id': 'the-cantidad-selector'})['max']

        if stock:
            stock = int(stock)
        else:
            stock = -1

        if 'LG' not in name.upper().split(' '):
            stock = 0

        normal_price = Decimal(
            soup.find('p', 'price').find('span', 'amount').text
                .replace('Gs.', '').replace('.', '').strip())
        offer_price = Decimal(
            soup.find('p', 'price')
                .find('span', {'id': 'elpreciocentralPorta'}).text
                .split('Gs.')[-1].replace('.', '').replace('!', '').strip())

        if normal_price < offer_price:
            offer_price = normal_price

        description = html_to_markdown(
            str(soup.find('div', {'itemprop': 'description'})))

        pictures = soup.findAll('div', 'thumbnails-single owl-carousel')
        picture_urls = []

        for picture in pictures:
            picture_url = picture.find('a')['href']
            picture_urls.append(picture_url)

        return [Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'PYG',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )]
