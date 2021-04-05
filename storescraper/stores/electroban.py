from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Electroban(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != 'Television':
            return []

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) ' \
            'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.149 ' \
            'Safari/537.36'

        product_urls = []
        page = 1

        while True:
            if page >= 15:
                raise Exception('Page overflow')
            # Only get LG products
            url_webpage = 'https://www.electroban.com.py/buscar_' \
                          'paginacion.php?query=LG&page={}'.format(page)

            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('li', 'product')

            if not product_containers:
                break

            for product in product_containers:
                product_url = product.find('a')['href']
                if 'LG' in product_url:
                    product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) ' \
            'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.149 ' \
            'Safari/537.36'
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()
        sku_container = soup.find('a', 'single_add_to_cart_button')

        if not sku_container:
            sku = soup.find('input', {'id': 'aux_cod_articulo'})['value']
        else:
            sku = sku_container['href']

        stock_container = soup.find('div', 'availability')

        if not stock_container:
            stock = -1
        else:
            stock = stock_container.find('span').text.split(' ')[0]
            if stock == 'Sin':
                stock = 0
            else:
                stock = int(stock)

        if 'LG' not in name.upper().split(' '):
            stock = 0

        post_data = 'plazo=CONTADO&cod_articulo={}'.format(sku)

        session.headers['Content-Type'] = 'application/x-www-form' \
                                          '-urlencoded; charset=UTF-8'

        price = soup.find('span', {'id': 'elpreciocentral'}) \
            .text.replace('Gs.', '').replace('.', '').strip()

        if not price:
            price = Decimal(session.post(
                'https://www.electroban.com.py/ajax/calculo_plazo.php',
                data=post_data).text)
        else:
            price = Decimal(price)

        picture_urls = [soup.find(
            'div', 'thumbnails-single owl-carousel').find('a')['href']]

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
            picture_urls=picture_urls
        )]
