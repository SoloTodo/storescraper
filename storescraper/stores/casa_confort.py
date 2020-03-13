import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class CasaConfort(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Refrigerator',
            'Oven',
            'AirConditioner',
            'WashingMachine',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('video/led_estandar', 'Television'),
            ('audio/sistemas_de_sonido', 'StereoSystem'),
            ('audio/bocinas', 'StereoSystem'),
            ('linea-blanca/lavadoras', 'WashingMachine'),
            ('linea-blanca/secadoras', 'WashingMachine'),
            ('linea-blanca/refrigeradoras', 'Refrigerator'),
            ('linea-blanca/congeladores', 'Refrigerator'),
            ('linea-blanca/hornos', 'Oven'),
            ('linea-blanca/microondas', 'Oven'),
            ('aires-acondicionados', 'AirConditioner'),
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.54.0'
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 20:
                    raise Exception('Page overflow: ' + category_path)

                category_url = 'https://www.casaconfort.net/' \
                               'categoria-producto/{}/page/{}/' \
                               ''.format(category_path, page)

                response = session.get(category_url)

                if response.status_code in [404]:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                for container in soup.findAll('li', 'isotope-item'):
                    if 'LG' not in container.find('h4').text.upper():
                        continue
                    product_urls.append(container.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.54.0'
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()

        sku_container = soup.find('span', {'itemprop': 'sku'})

        if sku_container:
            sku = sku_container.text.strip()
        else:
            sku = soup.find('input', {'id': 'comment_post_ID'})['value']

        if soup.find('link', {'itemprop': 'availability'})['href'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('meta', {'itemprop': 'price'})['content'])

        description = html_to_markdown(
            str(soup.find('div', {'itemprop': 'description'})))

        picture_urls = [tag.find('a')['href'] for tag in
                        soup.findAll('div',
                                     'woocommerce-product-gallery__image')]

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
            'USD',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )]
