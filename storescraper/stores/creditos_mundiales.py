from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class CreditosMundiales(Store):
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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            # ('linea-blanca/aires-acondicionados', 'AirConditioner'),
            ('linea-blanca/lavadoras', 'WashingMachine'),
            ('linea-blanca/refrigeradora', 'Refrigerator'),
            ('linea-blanca/congeladores', 'Refrigerator'),
            ('linea-blanca/hornos', 'Oven'),
            ('electronica/televisores', 'Television'),
            ('electronica/equipos-de-sonido', 'StereoSystem'),
            # ('electronica/reproductores-de-video', 'OpticalDiskPlayer'),
            # ('celulares/movil', 'Cell'),
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            url = 'http://creditosmundiales.com/{}/'.format(category_path)
            print(url)
            soup = BeautifulSoup(session.get(url).text, 'html.parser')

            product_containers = soup.findAll('li', 'product')

            if not product_containers:
                raise Exception('Empty category: ' + category_path)

            for container in product_containers:
                if 'LG' not in container.find('h2').text.upper():
                    continue
                product_urls.append(container.find('a')['href'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()
        sku = soup.find('span', 'sku').text.strip()

        price = Decimal(soup.find('span', 'contado').find(
            'span', 'attribute-value').text)

        picture_urls = [tag['href'] for tag in soup.find(
            'figure', 'woocommerce-product-gallery__wrapper').findAll('a')]
        description = html_to_markdown(str(
            soup.find('div', 'woocommerce-Tabs-panel--description')))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
