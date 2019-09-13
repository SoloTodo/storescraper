from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.store import Store
from storescraper.product import Product
from storescraper.utils import html_to_markdown, session_with_proxy


class EightBits(Store):
    @classmethod
    def categories(cls):
        return [
            'VideoGameConsole'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['Consola-PS4', 'VideoGameConsole'],
            ['Consola-3DS', 'VideoGameConsole'],
            ['Consolas-2DS', 'VideoGameConsole'],
            ['nintendo-switch-consolas', 'VideoGameConsole'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.8-bits.cl/{}?limit=100&page={}'\
                    .format(category_path, page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('div', 'product-thumb')

                if not product_containers:
                    if page == 1:
                        raise Exception(
                            'Empty section {}'.format(category_path))
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        info_container = soup.find('div', 'product-info')

        name = info_container.find('h1').text.strip()
        sku = info_container.find('input', {'name': 'product_id'})['value']

        stock = -1
        if info_container.find('b', 'sin-stock'):
            stock = 0

        offer_price = Decimal(info_container.find(
            'span', 'price').text.replace('$', '').replace('.', ''))

        if info_container.find('span', 'normal_price'):
            normal_price = Decimal(info_container.find(
                'span', 'normal_price').text.replace('$', '').replace('.', ''))
        else:
            normal_price = offer_price

        picture_urls = [info_container.find('img')['src'].replace(' ', '%20')]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            picture_urls=picture_urls,
            description=description
        )

        return [p]
