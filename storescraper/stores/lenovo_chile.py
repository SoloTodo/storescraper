from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class LenovoChile(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Tablet'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)

        product_urls = []

        if category != 'Notebook':
            return []

        soup = BeautifulSoup(session.get(
            'https://www.lenovo.com/cl/es/ofertas/black-friday/').text,
                             'html.parser')

        for product_box in soup.findAll('div', 'product-box'):
            product_path = product_box.find(
                'p', 'product-title').find('a')['href']
            product_url = 'https://www.lenovo.com' + product_path
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'desktopHeader').text.strip()
        sku = soup.find('meta', {'name': 'productid'})['content'].strip()

        price_str = soup.find('meta', {'name': 'productprice'})['content']
        price = Decimal(remove_words(price_str))

        description = html_to_markdown(
                str(soup.find('div', {'id': 'tab-techspec'})))

        picture_urls = ['https://www.lenovo.com' +
                        soup.find('img', 'subSeries-Hero')['src']]

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
            part_number=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
