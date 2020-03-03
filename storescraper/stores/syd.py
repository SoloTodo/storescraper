import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Syd(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Ram',
            'Tablet',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://syd.cl'

        category_paths = [
            ['/collection/macbook-pro-13', 'Notebook'],
            ['/collection/macbook-pro-16', 'Notebook'],
            ['/collection/macbook-air', 'Notebook'],
            ['/collection/memorias', 'Ram'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = url_base + category_path

            response = session.get(category_url)

            if response.url != category_url:
                raise Exception('Invalid category: ' + category_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            titles = soup.findAll('div', 'bs-product')

            if not titles:
                raise Exception('Empty category: ' + category_url)

            for title in titles:
                product_link = title.find('a')
                product_url = url_base + product_link['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h2').text
        product_web_id = soup.find('input', {'id': 'productWebId'})['value']

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', 'zoom-img-trigger')]

        description = soup.find('div', 'row text-justify')
        description = description.findAll('p')
        description = html_to_markdown(str(description))

        variants_container = soup.find('select', {'id': 'variant'})
        products = []

        for variant in variants_container.findAll('option'):
            sku = variant['data-sku']
            part_number = sku
            price = Decimal(remove_words(variant['data-final_price']))

            variant_id = variant['value']

            stock_url = 'https://syd.cl/product/create/{}?q=1&' \
                        'productWebId={}'.format(variant_id, product_web_id)

            stock_data = json.loads(session.get(stock_url).text)
            if stock_data['status'] == 'ok':
                stock = -1
            else:
                stock = 0

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
                part_number=part_number,
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)

        return products
