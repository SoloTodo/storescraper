from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class AgenciasWayOnline(Store):
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
            ('productos/televisores', 'Television'),
            ('productos/audio', 'StereoSystem'),
            ('productos/tecnologia', 'Cell'),
            ('productos/linea-blanca', 'Refrigerator'),
            ('productos/electrodomesticos', 'Oven'),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            start = 0
            page = 1
            done = False

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.agenciaswayonline.com/guatemala/{}'\
                    .format(category_path)

                if start:
                    url += '?start={}'.format(start)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                for container in soup.findAll(
                        'div', 'vm-product-media-container'):
                    product_url = 'https://www.agenciaswayonline.com' \
                                  + container.find('a')['href']

                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)
                    start += 1

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')
        sku_container = soup.find('h4', 'codigo')

        if not sku_container:
            return []

        sku = sku_container.text.replace('Código: ', '')
        name = soup.find('h1', 'title-product-item').text
        stock = -1

        price = Decimal(soup.find('span', 'PricesalesPrice').text
                        .replace('Q', '').replace(',', ''))

        picture_urls = [tag['href'] for tag in soup.find
                        ('div', 'vm-product-media-container').findAll('a')]

        description = html_to_markdown(str(soup.find
                                           ('div', 'product-description')))

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
