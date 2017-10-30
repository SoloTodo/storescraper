from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Kuhn(Store):
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
            # ['iluminacionled/ampolletas-e27.html', 'Lamp'],
            # ['iluminacionled/ampolletas-gu10.html', 'Lamp'],
            # ['iluminacionled/ampolletas-e14.html', 'Lamp'],
            # Tubos LED
            ['iluminacionled/tubos.html', 'LightTube'],
            # Proyectores LED
            # ['iluminacionled/reflectores-led.html', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 '
                          'Safari/537.36'
        })

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.kuhn.cl/webstore/{}?limit=all'.format(
                category_path
            )

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            product_containers = soup.find(
                'ol', 'products-list').findAll('li', 'item')

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 '
                          'Safari/537.36'
        })

        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text.strip()
        sku = soup.find('input', {'name': 'product'})['value'].strip()

        if soup.find('button', {'id': 'product-addtocart-button'}):
            stock = -1
        else:
            stock = 0

        normal_price = Decimal(remove_words(
            soup.find('p', 'old-price').find('span', 'price').string))

        offer_price = Decimal(remove_words(
            soup.find('p', 'special-price').find('span', 'price').string))

        description = html_to_markdown(
            str(soup.find('div', 'short-description')))

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', 'ig_lightbox2')]

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
            picture_urls=picture_urls
        )

        return [p]
