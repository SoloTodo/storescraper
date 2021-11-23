from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Tupi(Store):
    @classmethod
    def categories(cls):
        return [
            'Television'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != 'Television':
            return []

        page = 1

        while True:
            url = 'https://www.tupi.com.py/buscar_paginacion.php?query=LG' \
                  '&page=' + str(page)

            if page >= 15:
                raise Exception('Page overflow: ' + url)

            print(url)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            product_containers = soup.findAll('div', 'product')

            if not product_containers:
                break

            for product in product_containers:
                product_link = product.findAll('a')[1]
                if 'lg' in product_link.text.lower():
                    product_urls.append(product_link['href'].replace('%', ''))

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()
        sku_container = soup.find(
            'meta', {'property': 'product:retailer_item_id'})

        if not sku_container:
            return []

        sku = sku_container['content']

        if not soup.find('input', {'id': 'the-cantidad-selector'}):
            return []

        stock = soup.find('input', {'id': 'the-cantidad-selector'})['max']

        if stock:
            stock = int(stock)
        else:
            stock = -1

        if 'LG' not in name.upper().split(' '):
            stock = 0

        price = Decimal(
            soup.find('p', 'monto_precio_contado').text.strip()
                .replace('Gs.', '').replace('.', '').strip())

        description = html_to_markdown(
            str(soup.find('div', {'itemprop': 'description'})))

        pictures = soup.findAll('div', 'thumbnails-single owl-carousel')
        picture_urls = []

        for picture in pictures:
            picture_url = picture.find('a')['href'].replace(' ', '%20')
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
