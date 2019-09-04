from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Jetstereo(Store):
    base_url = 'https://www.jetstereo.com'

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
            'Stove'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('tvs', 'Television'),
            ('audio-portatil', 'StereoSystem'),
            ('equipos-de-sonido', 'StereoSystem'),
            ('teatros-en-casa', 'StereoSystem'),
            ('smartphones', 'Cell'),
            ('refrigeradoras-side-by-side', 'Refrigerator'),
            ('refrigeradoras-french-door', 'Refrigerator'),
            ('refrigeradoras-twin', 'Refrigerator'),
            ('refrigeradora-top-mount', 'Refrigerator'),
            ('microondas', 'Oven'),
            ('hornos', 'Oven'),
            ('aire-acondicionado', 'AirConditioner'),
            ('twinwash', 'WashingMachine'),
            ('lavadoras-top-load', 'WashingMachine'),
            ('lavadora-carga-frontal', 'WashingMachine'),
            ('secadoras', 'WashingMachine'),
            ('estufas-electricas', 'Stove'),
            ('estufas-de-gas', 'Stove')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            url = '{}/{}?pv=1000'.format(cls.base_url, category_path)
            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            containers = soup.findAll('div', 'product-slide-entry')

            if not containers:
                raise Exception('Empty category: ' + url)

            for container in containers:
                product_url = '{}{}'\
                    .format(cls.base_url, container.find('a')['href'])
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url, allow_redirects=False)

        if data.status_code == 302:
            return []

        soup = BeautifulSoup(data.text, 'html.parser')

        sku_container = soup.find('div', 'star')

        if not sku_container:
            return []

        sku = sku_container.find('h4').text.replace('SKU: ', '').strip()

        name = '{} ({})'\
            .format(soup.find('div', 'article-container').find('h1').text, sku)

        if soup.find('div', 'share-box').find('a', 'add-to-cart-btn'):
            stock = -1
        elif soup.find('span', 'text-available-stores').text.strip() != '':
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('div', 'price').find('div', 'current')
                        .text.strip().replace('L. ', '').replace(',', ''))

        picture_urls = []
        pictures = soup.findAll('div', 'product-zoom-image')

        for picture in pictures:
            picture_url = picture.find('img')['src'].replace(' ', '%20')
            if 'https:' not in picture_url:
                picture_url = '{}{}'.format(cls.base_url, picture_url)
            picture_urls.append(picture_url)

        description = html_to_markdown(str(soup.find('ul', 'read-more-wrap')))

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
