from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class AlmacenesJapon(Store):
    @classmethod
    def categories(cls):
        return [
            'StereoSystem',
            'AirConditioner',
            'Oven',
            'WashingMachine',
            'Cell',
            'Television',
            'Monitor',
            'Refrigerator',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['audio-parlantes-920', 'StereoSystem'],
            ['audio-mini-componentes-918', 'StereoSystem'],
            ['climatizacion-aire-acondicionado-924', 'AirConditioner'],
            ['cocina-cocina-a-gas-929', 'Oven'],
            ['electromenores-coccion-940', 'Oven'],
            ['lavado-y-secado-lavadoras-946', 'WashingMachine'],
            ['lavado-y-secado-secadoras-948', 'WashingMachine'],
            ['tecnologia-celulares-956', 'Cell'],
            ['tv-y-video-televisores-964', 'Television'],
            ['tv-y-video-monitores-comerciales-1043', 'Monitor'],
            ['refrigeracion-refrigeradores-950', 'Refrigerator']
        ]

        session = session_with_proxy(extra_args)
        base_url = 'https://www.almacenesjapon.com/shop/category/{}?' \
                   'brands=LG-510'
        product_urls = []

        for url_extension, local_category in category_paths:
            if category != local_category:
                continue

            url = base_url.format(url_extension)
            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            product_containers = soup.find('div', {'id': 'products_grid'})

            if not product_containers:
                raise Exception('Empty path: ' + url)

            products = product_containers.findAll('div', {'id': 'grid_list'})

            for product in products:
                product_url = 'https://www.almacenesjapon.com{}'.format(product.find('a')['href'])
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 403:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('h1', 'product-detail-name').text.strip()
        sku = soup.find('span', 'item-code').text.strip()
        stock = 0

        if soup.find('link', {'itemprop': 'availability'})['href'] == 'https://schema.org/InStock':
            stock = -1

        price = Decimal(
            soup.find('span', {'itemprop': 'price'}).text)

        picture_urls = [soup.find('meta', {'itemprop': 'image'})['content']]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'full_spec'})))

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
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
