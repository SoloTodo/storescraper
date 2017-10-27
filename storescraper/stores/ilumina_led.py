from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class IluminaLed(Store):
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
            ['producto-categoria/ampolletas-led/', 'Lamp'],
            # Tubos LED
            ['producto-categoria/tubos-led/', 'LightTube'],
            # Proyectores LED
            ['producto-categoria/proyectores-de-area/', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.iluminaled.cl/{}?count=100&paged=' \
                           ''.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            product_containers = soup.findAll('li', 'product')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        name = soup.find('h1', 'product_title').text.strip()
        sku = soup.find('span', 'add_to_wishlist')['data-product-id'].strip()

        price = Decimal(soup.find('meta', {'itemprop': 'price'})['content'])

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        picture_urls = [soup.find('meta', {'property': 'og:image'})['content']]

        if soup.find('button', 'single_add_to_cart_button'):
            stock = -1
        else:
            stock = 0

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
