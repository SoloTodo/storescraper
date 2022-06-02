from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class AgenciasWayOnline(Store):
    preferred_products_for_url_concurrency = 1
    preferred_discover_urls_concurrency = 1

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
            ('categoria/televisores', 'Television'),
            ('categoria/audio', 'StereoSystem'),
            ('categoria/tecnologia/celulares', 'Cell'),
            ('categoria/linea-blanca/refrigeradoras', 'Refrigerator'),
            ('categoria/linea-blanca/congeladores', 'Refrigerator'),
            ('categoria/linea-blanca/horno-microondas', 'Oven'),
            ('categoria/linea-blanca/lavadoras', 'WashingMachine')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 15:
                    raise Exception('Page overflow')

                url = 'https://agenciaswayonline.com/{}/page/{}/'\
                    .format(category_path, page)

                soup = BeautifulSoup(session.get(url, timeout=20).text,
                                     'html.parser')

                products_container = soup.find('div', 'wrap-products')

                if not products_container:
                    if page == 1:
                        raise Exception('Empty path: {}'.format(url))
                    break

                products = products_container.findAll('div', 'block-item')

                for product in products:
                    if product.find('img', {'alt': 'LG'}):
                        product_url = product.find('a')['href']
                        product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url, timeout=20).text
        soup = BeautifulSoup(data, 'html.parser')

        product_container = soup.find('div', 'detail-product')

        if not product_container:
            return []

        sku = product_container['id'].split('-')[1]

        model = product_container.find(
            'p', 'alter').text.split(
            'Alterno')[0].split(':')[1].strip()

        name = '{} - {} ({})'.format(
            product_container.find('h3').text.strip(),
            product_container.find('h1').text.strip(),
            model)

        stock = -1

        price = Decimal(product_container.find(
            'h6').text.replace('Q', '').replace(',', ''))

        picture_urls = [product_container.find('img')['data-large_image']]

        description = html_to_markdown(str(product_container.find('ul')))

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
