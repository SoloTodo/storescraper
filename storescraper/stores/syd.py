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
        url_base = 'http://www.syd.cl'

        category_paths = [
            ['/computadoras/macbook_pro_13', 'Notebook'],
            ['/computadoras/macbook_pro_15', 'Notebook'],
            ['/computadoras/macbook_air', 'Notebook'],
            # ['/computadoras/monitores', 'Monitor'],
            ['/memorias', 'Ram'],
            ['/ipodiphoneipad/ipad_mini', 'Tablet'],
            # ['/ipodiphoneipad/ipad_retina', 'Tablet'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = url_base + category_path + '/?op=all&crit='

            response = session.get(category_url)

            if response.url != category_url:
                raise Exception('Invalid category: ' + category_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            titles = soup.findAll('h4')

            if not titles:
                raise Exception('Empty category: ' + category_url)

            for title in titles:
                product_link = title.find('a')
                product_url = url_base + category_path + '/' + \
                    product_link['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.findAll('h2')[4].text.strip()
        sku = soup.find('input', {'name': 'sku'})['value'].strip()
        part_number = soup.find('div', 'descripcion').find(
            'h3').text.split(':')[1].strip()

        price = soup.find('div', 'detallesCompra')
        price = price.findAll('dd')[1].string
        price = Decimal(remove_words(price))

        description = html_to_markdown(str(soup.find('div', 'texto')))

        picture_urls = ['http://www.syd.cl' +
                        soup.find('div', 'imagenProducto').find('img')['src']]

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
            'CLP',
            sku=sku,
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
