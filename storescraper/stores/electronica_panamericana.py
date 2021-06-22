import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class ElectronicaPanamericana(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only gets LG products

        if category != 'Television':
            return []

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'

        product_urls = []
        url = 'https://electronicapanamericana.com/marcas/lg/?' \
              'product_count=1000&avia_extended_shop_select=yes'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for container in soup.findAll('li', 'product'):
            product_url = container.find('a')['href']
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html5lib')

        sku = soup.find('span', 'sku')

        if not sku:
            sku_container = soup.find(
                'script', {'type': 'application/ld+json'}).text
            sku_json = json.loads(sku_container)
            sku = str(sku_json['@graph'][1]['sku'])
        else:
            sku = sku.text.strip()

        name = '{} - {}'.format(
            sku, soup.find('h1', 'product_title').text.strip())[:255]

        if soup.find('p', 'out-of-stock'):
            stock = 0
        else:
            stock = -1

        price_container = soup.find('span', 'woocommerce-Price-amount')
        price = Decimal(price_container.text.replace('Q', '').replace(',', ''))

        picture_urls = [tag.find('a')['href'] for tag in soup.findAll(
            'div', 'woocommerce-product-gallery__image')]
        description = html_to_markdown(
            str(soup.find('div', 'woocommerce-Tabs-panel--description')))

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
            'GTQ',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
