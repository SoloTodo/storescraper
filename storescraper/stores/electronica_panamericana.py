import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class ElectronicaPanamericana(Store):
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
            'Headphones',
            'Monitor',
            'Projector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('audio-y-video/televisor/lg/', 'Television'),
            ('audio-y-video/televisor/rca/', 'Television'),
            ('audio-y-video/televisor/samsung/', 'Television'),
            ('audio-y-video/reproductores/', 'OpticalDiskPlayer'),
            ('audio-y-video/tv-audio/', 'StereoSystem'),
            ('hogar/ambiente/', 'AirConditioner'),
            ('hogar/coccion/', 'Stove'),
            ('hogar/refrigeracion/', 'Refrigerator'),
            ('hogar/lavanderia/', 'WashingMachine'),
            ('tecnologia/proyeccion/', 'Projector'),
            ('tecnologia/monitores/', 'Monitor'),
            ('celulares/', 'Cell'),
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

                url = 'https://electronicapanamericana.com/product-category/' \
                      '{}page/{}/'.format(category_path, page)
                print(url)
                response = session.get(url)

                if response.status_code == 404:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                for container in soup.findAll('li', 'product'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        sku = soup.find('span', 'sku')

        if not sku:
            sku_container = soup.find(
                'script', {'type': 'application/ld+json'}).text
            sku_json = json.loads(sku_container)
            sku = str(sku_json['@graph'][1]['sku'])

        else:
            sku = sku.text.strip()

        name = '{} ({})'.format(
            soup.find('h1', 'product_title').text.strip(), sku)

        if soup.find('p', 'out-of-stock'):
            stock = 0
        else:
            stock = -1

        price_container = soup.find('span', 'woocommerce-Price-amount')
        price = Decimal(price_container.text.replace('Q', '').replace(',', ''))

        picture_urls = [tag.find('a')['href'] for tag in soup.findAll(
            'div', 'woocommerce-product-gallery__image')]
        description = html_to_markdown(
            str(soup.find('div', 'woocommerce-Tabs-panel--description')))

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
            'GTQ',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
