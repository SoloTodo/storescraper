import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Vitel(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightProjector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'http://www.vitel.cl/'

        category_paths = [
            # Ampolletas LED
            ['iluminacion/lamparas-tubos-led', 'Lamp'],
            # Proyectores LED con DS43
            # ['iluminacion.html?cat=60', 'LightProjector'],
            # ['iluminacion.html?cat=318', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = base_url + category_path
            print(category_url)
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            product_containers = soup.findAll('li', 'product-items')

            if not product_containers:
                raise Exception('Emtpy category: ' + category_url)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()

        price_container = soup.find('span', 'price-wrapper')

        if not price_container:
            return []

        price = Decimal(price_container['data-price-amount'])

        price *= Decimal('1.19')
        price = price.quantize(0)

        description = html_to_markdown(str(soup.find('div', 'description')))

        picture_urls = [soup.find('meta', {'property': 'og:image'})['content']]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
