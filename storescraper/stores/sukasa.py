from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Sukasa(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'Television',
            'StereoSystem',
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['4232-refrigeradoras', 'Refrigerator'],
            ['72-microondas', 'Oven'],
            ['93-lavadoras', 'WashingMachine'],
            ['94-secadoras', 'WashingMachine'],
            ['95-lavadoras-y-secadoras-todo-en-1', 'WashingMachine'],
            ['309-televisores', 'Television'],
            ['2849-parlantes', 'StereoSystem'],
            ['4248-micro-y-mini-componentes', 'StereoSystem'],
            ['4249-barras-de-sonido-y-teatros-en-casa', 'StereoSystem'],
            ['4251-celulares-y-tablets', 'Cell']
        ]

        session = session_with_proxy(extra_args)
        base_url = 'https://www.sukasa.com/{}?q=Marca-LG'
        product_urls = []

        for url_extension, local_category in category_paths:
            if category != local_category:
                continue

            url = base_url.format(url_extension)
            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            products = soup.findAll('div', 'product-container')

            if not products:
                raise Exception('Empty path: ' + url)

            for product in products:
                product_url = product.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('h1', 'page-heading').text.strip()
        sku = soup.find('h2', 'reference-product').text.split(':')[1].strip()
        stock = -1

        price = Decimal(
            soup.find('span', {'itemprop': 'price'})
                .find('span').text.replace('$', ''))

        picture_urls = [
            a['data-zoom-image'] for a in soup.findAll('a', 'thumb')]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'collapseDescription'})))

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
