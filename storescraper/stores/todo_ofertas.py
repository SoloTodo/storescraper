import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TodoOfertas(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extension = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extension:
            if local_category != category:
                continue
            page = 0
            while True:
                if page > 10:
                    raise Exception('page overflow ')
                url_webpage = 'https://www.todoofertas.com.uy/productos' \
                              '/productos.php?id_marca=116&pagina={}'.format(
                                page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'contenedor_22').findAll(
                    'div', 'prod_item')
                if not product_containers:
                    if page == 0:
                        logging.warning('Empty category: ' + local_category)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.todoofertas.com.uy' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'nombre').text
        sku = soup.find('input', {'name': 'ids[]'})['value']
        if soup.find('div', 'opcionescarrito').find('input', 'submit2'):
            stock = -1
        else:
            stock = 0
        price = Decimal(soup.find('div', 'precios_cont').find('span', {
            'id': 'precio_ent_actual'}).text)
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'gal_fotos_chicas_cont').findAll(
                            'img')]
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
            'USD',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
