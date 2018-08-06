from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words


class ProMovil(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['6-smartphones', 'Cell'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.promovil.cl/{}?n=250&p={}'.format(
                    category_path, page)

                print(category_url)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                response = session.get(category_url)

                if response.url != category_url:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    else:
                        break

                soup = BeautifulSoup(response.text, 'html.parser')

                products_containers = soup.findAll('div', 'ajax_block_product')

                for product_container in products_containers:
                    product_url = product_container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('input', {'name': 'id_product'})['value']

        offer_price = Decimal(remove_words(
            soup.find('span', {'id': 'our_price_display'}).text))

        normal_price_container = soup.find(
            'span', {'id': 'unit_price_display'})

        if normal_price_container:
            normal_price = Decimal(remove_words(normal_price_container.text))
            if normal_price < offer_price:
                normal_price = offer_price
        else:
            normal_price = offer_price

        stock = int(soup.find('span', {'id': 'quantityAvailable'}).text)

        if stock < 0:
            stock = 0

        description = html_to_markdown(
            str(soup.find('div', 'pb-center-column')))

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'fancybox')]

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
            sku=sku,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
