from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Iprotech(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'VideoGameConsole',
            'Wearable'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('tienda/smartphones/samsung/', 'Cell'),
            ('tienda/smartphones/iphone/', 'Cell'),
            ('tienda/smartphones/motorola/', 'Cell'),
            ('tienda/smartphones/xiaomi/', 'Cell'),
            ('cat/', 'Cell'),
            ('tienda/smartphones/sony/', 'Cell'),
            ('tienda/smartphones/lg/', 'Cell'),
            ('tienda/smartphones/huawei/', 'Cell'),
            ('tienda/consolas/', 'VideoGameConsole'),
            ('tienda/smartwatch-y-chromecast/', 'Wearable')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            url = 'https://iprotech.cl/{}'.format(category_path)
            soup = BeautifulSoup(session.get(url).text, 'html.parser')

            for container in soup.findAll('div', 'product-thumb'):
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        sku = soup.find('span', 'sku').text
        name = soup.find('h1', 'product_title').text
        stock = soup.find('p', 'stock').find('span').text\
            .replace('In Stock', '').strip()

        if stock:
            stock = int(stock)
        else:
            stock = 0

        price_container = soup.find('p', 'price').find('ins')

        if not price_container:
            price_container = soup.find('p', 'price')

        price = Decimal(price_container.find('span', 'amount').contents[1]
                        .replace('.', ''))
        offer_prices_chunks = soup.findAll('span', 'efectivo2')
        offer_price = ''

        for chunk in offer_prices_chunks:
            offer_price += chunk.contents[0]

        offer_price = Decimal(offer_price.replace('$', '').replace('.', ''))

        if offer_price > price:
            offer_price = price

        picture_urls = []
        picture_containers = soup\
            .findAll('div', 'woocommerce-product-gallery__image')

        for picture in picture_containers:
            picture_urls.append(picture.find('a')['href'])

        description = html_to_markdown(str(
            soup.find('div', {'id': 'tab-description'})))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
