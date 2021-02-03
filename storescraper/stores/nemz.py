import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MONITOR, KEYBOARD, \
    COMPUTER_CASE, MOUSE, KEYBOARD_MOUSE_COMBO, GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Nemz(Store):
    @classmethod
    def categories(cls):
        return {
            HEADPHONES,
            MONITOR,
            KEYBOARD,
            COMPUTER_CASE,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            GAMING_CHAIR
        }

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['monitores', MONITOR],
            ['teclados', KEYBOARD],
            ['gabinetes', COMPUTER_CASE],
            ['mouse', MOUSE],
            ['combos-gamer', KEYBOARD_MOUSE_COMBO],
            ['sillas-gamer', GAMING_CHAIR]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.nemz.cl/product-category/{}/page' \
                              '/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty cagtegory: ' + url_extension)
                    break
                for container in product_containers.findAll('li'):
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
        name = soup.find('h1', 'product_title').text
        pn_container = soup.find('span', 'sku')

        if pn_container:
            name += ' ({})'.format(pn_container.text.strip())

        sku = soup.find('input', {'name': 'queried_id'})['value']
        description_tag = soup.find(
            'div', 'woocommerce-product-details__short-description')

        if description_tag and 'PREVENTA' in description_tag.text.upper():
            stock = 0
        elif soup.find('p', 'stock'):
            stock = 0
        elif soup.find('span', 'stock'):
            stock = int(soup.find('span', 'stock').text.split()[0])
        else:
            return []
        price_container = soup.find('p', 'price')
        if price_container.find('ins'):
            price = Decimal(remove_words(price_container.find('ins').text
                                         .strip()))
        elif price_container.find('bdi'):
            price = Decimal(remove_words(price_container.find('bdi').text
                                         .strip()))
        else:
            return []
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'woocommerce-product-gallery')
                            .findAll('img')]
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
            picture_urls=picture_urls
        )
        return [p]
