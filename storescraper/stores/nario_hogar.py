import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class NarioHogar(Store):
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
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://www.nariohogar.com.uy/producto' \
                          '/busqueda?name=lg'
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('a', 'overlay small')
            if not product_containers:
                break
            for container in product_containers:
                product_url = container['href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'page-title').text.strip()
        sku = url.split('/')[-1]
        stock = -1
        price = Decimal(soup.find('div', 'price-detalle').text.split()[-1])
        picture_urls = [urllib.parse.quote(tag['src'], safe='/:') for tag in
                        soup.find('div', 'owl-carousel').findAll('img')]
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
