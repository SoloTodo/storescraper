import re

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Byp(Store):
    preferred_products_for_url_concurrency = 3

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
            ['ampolletas/led', 'Lamp'],
            # Tubos LED
            ['tubos/led', 'LightTube'],
            # Proyectores LED
            ['led/iluminacion-profesional-led', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + category_path)

                category_url = 'https://www.byp.cl/{}?limit=72&p={}'.format(
                    category_path, page
                )

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                product_containers = soup.find(
                    'ul', 'products-grid').findAll('li', 'item')

                done = False
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break

                    product_name = container.find('h2').find('a').text.lower()

                    if local_category == 'LightProjector' and \
                            'proyector' not in product_name:
                        continue

                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        pricing_text = re.search(
            r'(\'sku\': [\S\s]+)ga\(', page_source)

        pricing_text = '{' + pricing_text.groups()[0]
        pricing_json = demjson.decode(pricing_text)

        name = pricing_json['Name']
        sku = pricing_json['sku']
        normal_price = Decimal(round(float(pricing_json['Price']) * 1.19))
        offer_price = normal_price
        stock = int(float(pricing_json['stock']))

        if stock > 0:
            stock = -1

        description = html_to_markdown(str(soup.find('div', 'panel')))

        picture_urls = [link['href'] for link in
                        soup.findAll('a', 'cloud-zoom-gallery')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
