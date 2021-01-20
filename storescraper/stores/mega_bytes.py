import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PROCESSOR, MOTHERBOARD, VIDEO_CARD, RAM, \
    SOLID_STATE_DRIVE, COMPUTER_CASE, MONITOR, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class MegaBytes(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            MOTHERBOARD,
            VIDEO_CARD,
            RAM,
            SOLID_STATE_DRIVE,
            COMPUTER_CASE,
            MONITOR,
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['procesadores-cpu', PROCESSOR],
            ['placa-madre', MOTHERBOARD],
            ['tarjeta-de-video', VIDEO_CARD],
            ['memorias-ram', RAM],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['hardware', COMPUTER_CASE],
            ['monitores', MONITOR],
            ['accesorios', KEYBOARD]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            done = False
            while not done:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://megabytes.cl/{}/page/{}/'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_box = soup.find('ul', 'wc-block-grid__products')

                if not product_box:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                product_containers = product_box.findAll(
                    'a', 'wc-block-grid__product-link')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers:
                    product_url = container['href']
                    if product_url in product_urls:
                        done = True
                        break
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
        sku = soup.find('button', 'single_add_to_cart_button button alt')[
            'value']
        stock = -1
        offer_price = Decimal(
            remove_words(soup.find('p', 'price').text).split()[-1])
        price_container = soup.find('div',
                                    'woocommerce-product-details__short'
                                    '-description')
        if price_container and price_container.find('strong'):
            normal_price = Decimal(
                remove_words(price_container.find('strong').text))
        elif price_container and price_container.find('span'):
            normal_price = Decimal(
                remove_words(price_container.find('span').text))
        else:
            normal_price = offer_price

        picture_urls = [tag['data-src'] for tag in
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
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls[1:]
        )
        return [p]
