import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class PackardBell(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Tablet'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['catalogo/127-Notebooks.html', 'Notebook'],
            ['cyberday', 'Notebook'],
            ['catalogo/176-Ultradelgado.html', 'Notebook'],
            ['catalogo/175-Gamer.html', 'Notebook'],
            ['catalogo/171-Convertible.html', 'Notebook'],
            ['catalogo/146-Monitores.html', 'Monitor'],
            ['catalogo/145-Tablets.html', 'Tablet'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            category_url = 'http://www.netnow.cl/' + category_path

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            links = soup.findAll('a', 'Producto_Detalles')

            if not links:
                raise Exception('Empty category: ' + category_url)

            for link in links:
                product_urls.append(link['href'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('div', 'dnombre_producto').text.strip()
        sku = soup.find('input', {'name': 'idProducto'})['value'].strip()
        stock = int(re.search(
            'Stock : (\d+)', soup.find(
                'div', 'ddiferencia_precio').text).groups()[0])

        price = soup.find('div', 'dprecio_oferta').contents[1]
        price = Decimal(remove_words(price))

        description = html_to_markdown(
            str(soup.find('div', {'id': 'Caracteristicas'})))

        picture_urls = []
        for tag in soup.find('div', 'imagen_galeria').findAll('a'):
            picture_url = re.search(r"largeimage: '(.+?)'",
                                    str(tag)).groups()[0]
            picture_urls.append(picture_url)

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
