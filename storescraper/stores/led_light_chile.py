import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LedLightChile(Store):
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
            ['hogar/ampolletas', 'Lamp'],
            # Proyectores LED
            ['hogar/proyectores', 'LightProjector'],
            # Tubos LED
            ['hogar/equipos-y-tubos', 'LightTube'],
        ]

        discovery_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://ledlightchile.cl/categoria-producto/{}' \
                           ''.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            product_containers = soup.findAll('div', 'wf-cell')

            for container in product_containers:
                subcategory_url = container.find('a')['href']
                discovery_urls.append(subcategory_url)

        return discovery_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        products = []

        variations_container = soup.find('form', 'variations_form')

        variations = json.loads(variations_container[
                                    'data-product_variations'])
        print(variations)

        for variation in variations:
            field_names = [
                'attribute_pa_caracteristicas-tecnicas',
                'attribute_pa_caracteristicas-tecnicas-2',
                'attribute_pa_caracteristicas-tecnicas-3',
                None
            ]

            field_name = None

            for field_name in field_names:
                if field_name in variation['attributes']:
                    break

            if field_name:
                name = variation['attributes'][field_name].replace(
                    '%e2%80%a2', '')
            else:
                name = soup.find('meta', {'property': 'og:title'})['content']
            sku = str(variation['variation_id'])

            price = variation['display_price']
            if not price:
                continue
            price = Decimal(price)

            if variation['is_purchasable']:
                stock = -1
            else:
                stock = 0

            picture_urls = [variation['image']['url']]

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
                picture_urls=picture_urls
            )

            products.append(p)

        return products
