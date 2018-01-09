from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy,\
    remove_words, html_to_markdown


class ClimaSeguro(Store):
    @classmethod
    def categories(cls):
        return [
            'AirConditioner',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('page-split-muro.asp', 'AirConditioner'),
        ]

        product_urls = []

        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.climaseguro.cl/' + category_path

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            product_cells = soup.findAll('div', 'prd-element-item')

            for product_cell in product_cells:
                product_url = 'https://www.climaseguro.cl'\
                              + product_cell.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text

        sku = soup.find('input', {'id': 'form-input-producto'})['value']

        if soup.find('h3').text == 'No products found':
            stock = 0
        else:
            stock = -1

        price = Decimal(remove_words(soup.find(
            'span', {'id': 'precio_venta_tienda'}).text))

        description = html_to_markdown(str(soup.find('div', {'id': 'home'})))

        picture_urls = ['https://www.climaseguro.cl' +
                        soup.find('div', 'box-details-product').img['src']]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
