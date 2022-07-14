import json
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
                              '0,0,LG,0,0,0,rel,%5B%22Lg%22%5D,false,' \
                              '%5B%5D,%5B%5D,,{}'.format(page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', {'id': 'SECTION1'}). \
                    findAll('div', 'card-product-section')
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
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, 'html5lib')
        json_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        name = json_data['name']
        description = json_data['description']
        sku = json_data['offers']['sku']
        price = Decimal(json_data['offers']['price'])

        if json_data['offers']['availability'] == 'https://schema.org/InStock':
            stock = -1
        else:
            stock = 0

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
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
