from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import HEADPHONES, TABLET, TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TicOnlineStore(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            TABLET,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['22-televisores', TELEVISION],
            ['23-tablet', TABLET],
            ['4-accesorios-para-computadores', HEADPHONES],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://tic-online-store.cl/{}?' \
                              'page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_section = soup.find('section', {'id': 'products-list'})
                product_containers = product_section.findAll(
                    'div', 'item-product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('h1', 'namne_details').text.strip()
        key = soup.find('input', {'id': 'product_page_product_id'})['value']

        sku_p = soup.find('p', 'reference')
        if sku_p:
            sku = sku_p.find('span').text.strip()
        else:
            sku = None

        price = Decimal(soup.find('span', {'itemprop': 'price'})['content'])

        cart_btn = soup.find('button', 'add-to-cart')
        if cart_btn:
            qty_div = soup.find('div', 'product-quantities')
            if qty_div:
                stock = int(qty_div.find('span')['data-stock'])
            else:
                stock = -1
        else:
            stock = 0

        picture_urls = []
        container = soup.find('div', 'product-view_content')
        for a in container.findAll('a'):
            picture_urls.append(a['href'])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls
        )
        return [p]
