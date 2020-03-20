import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TiendaSmart(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Tablet',
            'Headphones',
            'StereoSystem',
            'Wearable',
            'CellAccesory'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['3-smartphones.html', 'Cell'],
            ['tablets.html', 'Tablet'],
            ['audios/portipo/auriculares.html', 'Headphones'],
            ['wearabless.html', 'Wearable'],
            ['accesorios.html', 'CellAccesory'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                category_url = 'https://tiendasmart.cl/{}?' \
                               'p={}&product_list_limit=30'\
                    .format(category_path, page)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')
                product_containers = soup.findAll(
                    'div', 'product-hover')

                done = False

                if not product_containers:
                    raise Exception('Empty category: ' + category_url)

                for container in product_containers:
                    product_url = container.find(
                        'a', 'product-item-photo')['href']
                    if product_url in product_urls:
                        done = True
                        break
                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        pricing_data = json.loads(
            soup.findAll(
                'script', {'type': 'application/ld+json'})[2].text.replace(
                '\n', ''))

        name = pricing_data['name']
        sku = pricing_data['sku']

        price = Decimal(pricing_data['offers'][0]['price'])

        if pricing_data['offers'][0]['availability'] == 'InStock':
            stock = -1
        else:
            stock = 0

        description = '\n\n'.join([html_to_markdown(str(panel)) for
                                   panel in soup.findAll('div', 'panel')])
        picture_urls = [pricing_data['image']]

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
            'CLP',
            sku=sku,
            part_number=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
