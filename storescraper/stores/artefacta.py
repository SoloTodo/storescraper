from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Artefacta(Store):
    @classmethod
    def categories(cls):
        return [
            'Stove',
            'Refrigerator',
            'WashingMachine',
            'AirConditioner',
            'StereoSystem',
            'Television'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['linea-blanca/cocinas', 'Stove'],
            ['linea-blanca/refrigeracion', 'Refrigerator'],
            ['linea-blanca/lavadoras-y-secadoras', 'WashingMachine'],
            ['climatizacion/aires-acondicionados', 'AirConditioner'],
            ['audio/minicomponentes', 'StereoSystem'],
            ['televisores/hd', 'Television'],
            ['televisores/4k', 'Television'],
        ]

        session = session_with_proxy(extra_args)
        base_url = 'https://www.artefacta.com/productos/{}?at_marca=LG'
        product_urls = []

        for url_extension, local_category in category_paths:
            if category != local_category:
                continue

            url = base_url.format(url_extension)
            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            products = soup.findAll('a', 'product-item-link')

            if not products:
                raise Exception('Empty path: ' + url)

            for product in products:
                try:
                    product_url = product['href']
                    product_urls.append(product_url)
                except KeyError:
                    continue

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('span', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()
        stock = -1

        price = Decimal(
            soup.find('span', {'data-price-type': 'finalPrice'})
                .find('span', 'price').text.replace('$', '').replace(',', ''))

        picture_urls = [soup.find('div', 'preloaded-image').find('img')['src']]

        description = html_to_markdown(
            str(soup.find('div', 'description')))

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
