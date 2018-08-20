import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class IluminaLed(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightTube',
            'LightProjector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Ampolletas LED
            ['producto-categoria/ampolletas-led/', 'Lamp'],
            # Tubos LED
            ['producto-categoria/tubos-led/', 'LightTube'],
            # Proyectores LED
            ['producto-categoria/proyectores-de-area/', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.iluminaled.cl/{}?count=100&paged=' \
                           ''.format(category_path)

            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            product_containers = soup.findAll('li', 'product')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        base_name = soup.find('h1', 'product_title').text.strip()
        description = html_to_markdown(str(soup.find('div', 'description')))

        variations_form = soup.find('form', 'variations_form')

        products = []

        if variations_form:
            variations_data = json.loads(
                variations_form['data-product_variations'])
            for variant_data in variations_data:
                name = '{} - {}'.format(
                    base_name,
                    variant_data['attributes']['attribute_pa_color'])
                sku = str(variant_data['variation_id'])

                if variant_data['is_purchasable']:
                    stock = -1
                else:
                    stock = 0

                price = Decimal(variant_data['display_price'])
                picture_urls = [variant_data['image_src']]

                products.append(Product(
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
                    description=description,
                    picture_urls=picture_urls
                ))
        else:
            name = base_name

            availability_container = \
                soup.find('link', {'itemprop': 'availability'})

            if availability_container['href'] == 'http://schema.org/InStock':
                stock = -1
            else:
                stock = 0

            sku = soup.find('input', {'name': 'add-to-cart'})

            if not sku:
                return []

            sku = sku['value']
            price = Decimal(
                soup.find('meta', {'itemprop': 'price'})['content'])
            picture_urls = [soup.find('img', 'woocommerce-main-image')['src']]

            products.append(Product(
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
                description=description,
                picture_urls=picture_urls
            ))

        return products
