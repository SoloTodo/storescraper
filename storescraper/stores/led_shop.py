from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class LedShop(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightTube',
            'LightProjector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Ampolletas LED
            ['?page_id=3&category=36', 'Lamp'],
            ['?page_id=3&category=76', 'Lamp'],
            ['?page_id=3&category=37', 'Lamp'],
            ['?page_id=3&category=38', 'Lamp'],
            ['?page_id=3&category=77', 'Lamp'],
            # ['?page_id=3&category=40', 'Lamp'],
            ['?page_id=3&category=41', 'Lamp'],
            ['?page_id=3&category=42', 'Lamp'],
            ['?page_id=3&category=96', 'Lamp'],
            ['?page_id=3&category=81', 'Lamp'],
            ['?page_id=3&category=71', 'Lamp'],
            ['?page_id=3&category=72', 'Lamp'],
            ['?page_id=3&category=39', 'Lamp'],
            ['?page_id=3&category=87', 'Lamp'],
            # Tubos LED
            ['?page_id=3&category=54', 'LightTube'],
            # Proyectores LED
            ['?page_id=3&category=60', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.ledshop.cl/' + category_path
            print(category_url)
            soup = BeautifulSoup(session.get(category_url, timeout=10).text,
                                 'html.parser')

            product_containers = soup.findAll('div', 'product_grid_item')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['Host'] = 'www.ledshop.cl'
        session.headers['User-Agent'] = 'curl/7.52.1'
        session.headers['Accept'] = '*/*'

        print(url)

        soup = BeautifulSoup(session.get(url, timeout=10).text, 'html.parser')
        name = soup.find('h2').text.strip()
        sku = soup.find('input', {'name': 'product_id'})['value'].strip()

        if soup.find('input', 'wpsc_buy_button'):
            stock = -1
        else:
            stock = 0

        try:
            price = Decimal(remove_words(soup.find(
                'div', 'wpsc_product_price').span.text))
        except InvalidOperation:
            price = Decimal(remove_words(soup.find(
                'div', 'wpsc_product_price').findAll('span')[1].text))

        price = price.quantize(0)

        description = html_to_markdown(
            str(soup.find('div', 'wpsc_description')))

        picture_urls = [tag['href'].replace(' ', '%20') for
                        tag in soup.findAll('a', 'thickbox')]

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
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
