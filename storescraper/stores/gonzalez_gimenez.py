from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class GonzalezGimenez(Store):
    @classmethod
    def categories(cls):
        return [
            'Television'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        base_url = 'https://www.gonzalezgimenez.com.py/{}'

        if category != 'Television':
            return []

        page = 1

        while True:
            url = 'https://www.gonzalezgimenez.com.py/catalogo.{}?q=LG'.format(
                page)

            if page >= 15:
                raise Exception('Page overflow: ' + url)

            print(url)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            product_containers = soup.find(
                'div', 'products').findAll('div', 'product')

            if not product_containers:
                break

            for product in product_containers:
                product_link = product.find('a')
                if 'LG' not in product_link['title'].upper():
                    continue

                product_url = 'https://www.gonzalezgimenez.com.py/' + \
                              product_link['href']
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()
        sku = soup.find('span', 'sku').text.strip()
        stock = -1

        if 'LG' not in name.upper().split(' '):
            stock = 0

        price_containers = soup.findAll('p', 'price')
        price_container = price_containers[0].find('ins')

        if not price_container:
            price_container = price_containers[1].find('ins')

        price = Decimal(
            price_container.find('span', 'amount').text
            .replace('₲.', '').replace('*', '').replace('.', '').strip())

        description = html_to_markdown(str(soup.find('div', 'tab-pane')))

        pictures = soup.findAll('div', 'woocommerce-product-gallery__image')
        picture_urls = []

        for picture in pictures:
            picture_url = picture.find('a')['data-src']
            picture_urls.append(picture_url)

        return [Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'PYG',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )]
