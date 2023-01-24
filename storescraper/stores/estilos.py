from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Estilos(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1
        while True:
            if page > 20:
                raise Exception('Page overflow')

            url_webpage = 'https://www.estilos.com.pe/54_lg?page={}'.format(
                page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')

            product_containers = soup.findAll('div', 'ajax_block_product')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category')
                break
            for container in product_containers:
                product_urls.append(container.find('a')['href'])
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if 'Este paquete contiene' in soup.text:
            return []

        product_data = json.loads(
            soup.find('div', {'id': 'product-details'})['data-product'])

        key = str(product_data['id'])
        name = product_data['name']
        sku = product_data['reference']
        price = Decimal(str(product_data['price_amount']))
        stock = product_data['quantity']
        picture_urls = [image['bySize']['large_default']['url'] for image in
                        product_data['images']]

        description_section = soup.find('section', 'product-features')
        if description_section:
            description = html_to_markdown(description_section.text)
        else:
            description = None

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'PEN',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
