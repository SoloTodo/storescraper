import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper.categories import NOTEBOOK, PRINTER, ALL_IN_ONE, MOUSE, \
    KEYBOARD, MONITOR, HEADPHONES


class ScGlobal(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            PRINTER,
            ALL_IN_ONE,
            MOUSE,
            KEYBOARD,
            MONITOR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Zbook
            ['117', NOTEBOOK],
            # Notebook
            ['119', NOTEBOOK],
            # Plotter
            ['120', PRINTER],
            # Notebook
            ['10', NOTEBOOK],
            # Rendimiento
            ['84', NOTEBOOK],
            # Hogar y Empresa
            ['18', NOTEBOOK],
            # Movilidad
            ['85', NOTEBOOK],
            # All In One
            ['115', ALL_IN_ONE],
            # Monitors
            ['15', MONITOR],
            # Impresoras
            ['11', PRINTER],
            # Teclados / Mouse
            ['123', MOUSE],
            # Audífonos
            ['125', HEADPHONES],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.scglobal.cl/index.php?' \
                               'controller=category&id_category={}&page={}' \
                               ''.format(category_path, page)
                print(category_url)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                response = session.get(category_url, verify=False)
                soup = BeautifulSoup(response.text, 'html.parser')

                if soup.find('section', 'page-not-found'):
                    if page == 1:
                        logging.warning('Empty category: ' + category_url)
                    break

                product_cells = soup.findAll('div', 'item-inner')

                for cell in product_cells:
                    product_url = cell.find('a')['href']
                    product_urls.append(product_url)

                page += 1

            product_urls.extend(product_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url, verify=False).text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value']

        pricing_container = soup.find('span', {'itemprop': 'price'})
        price = Decimal(pricing_container['content'])
        part_number = soup.find('span', {'itemprop': 'sku'}).text.strip()
        add_to_cart_button = soup.find('button', 'add-to-cart')

        if add_to_cart_button.get('disabled') is None:
            stock = -1
        else:
            stock = 0

        picture_urls = [tag.find('img')['data-image-large-src'] for tag in
                        soup.find('ul', 'product-images')
                            .findAll('li', 'thumb-container')]

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
            picture_urls=picture_urls
        )

        return [p]
