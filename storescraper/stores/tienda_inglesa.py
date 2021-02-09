from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TiendaInglesa(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        products_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 0
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + local_category)
                url_webpage = 'https://www.tiendainglesa.com.uy/busqueda?' \
                              '0,0,LG,0,0,0,,%5B%5D,false,%5B%5D,%5B%5D,,' \
                              '{}'.format(page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'div', 'gxwebcomponent gxwebcomponent-loading')
                if not product_containers:
                    break
                for container in product_containers:
                    products_url = container.find('a')['href']
                    products_urls.append(
                        'https://www.tiendainglesa.com.uy' + products_url)
                page += 1
        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'ProductNameFull').text.replace(
            '¡Envío Gratis!', '')
        sku = soup.find('span', 'wProductCodeInfo').text.split()[-1]
        stock = -1
        price = Decimal(
            soup.find('div', {'id': 'TXTPRICE'}).text.split()[1].replace(
                '.', ''))
        picture_urls = [
            soup.find('div', {'id': 'SECTION2'}).findAll('img')[1][
                'src'].split('?')[0]]
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
