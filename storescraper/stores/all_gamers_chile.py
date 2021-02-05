import html
import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import HEADPHONES, MOUSE, KEYBOARD, \
    KEYBOARD_MOUSE_COMBO, STEREO_SYSTEM, NOTEBOOK, TELEVISION, MONITOR, \
    VIDEO_GAME_CONSOLE, GAMING_CHAIR
from storescraper.utils import session_with_proxy, remove_words


class AllGamersChile(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            STEREO_SYSTEM,
            NOTEBOOK,
            TELEVISION,
            MONITOR,
            VIDEO_GAME_CONSOLE,
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios-gamer/headset', HEADPHONES],
            ['accesorios-gamer/mouse', MOUSE],
            ['accesorios-gamer/teclados', KEYBOARD],
            ['accesorios-gamer/set', KEYBOARD_MOUSE_COMBO],
            ['electronica/audio', STEREO_SYSTEM],
            ['electronica/notebook', NOTEBOOK],
            ['electronica/smart-tv', TELEVISION],
            ['electronica/monitores', MONITOR],
            ['consolas/nintendo-switch', VIDEO_GAME_CONSOLE],
            ['consolas/playstation', VIDEO_GAME_CONSOLE],
            ['consolas/xbox-one', VIDEO_GAME_CONSOLE],
            ['accesorios-gamer/sillas-gamer', GAMING_CHAIR],
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
                url_webpage = 'https://allgamerschile.com/categoria-producto' \
                              '/{}/page/{}/ '.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('article')
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
        if soup.find('h1', 'product_title'):
            name = soup.find('h1', 'product_title').text
        else:
            name = soup.find('h1', 'w-post-elm').text
        variants = soup.find('form', 'variations_form')
        if not variants:
            variants = soup.find('div', 'variations_form')

        if variants:
            products = []
            container_products = json.loads(
                html.unescape(variants['data-product_variations']))

            for product in container_products:
                variant_name = name + " - " + next(
                    iter(product['attributes'].values()))
                if product['is_in_stock']:
                    stock = int(product['max_qty'])
                else:
                    stock = 0
                sku = str(product['variation_id'])
                price = Decimal(product['display_price'])
                if product['image']['src'] == '':
                    picture_urls = [tag['src'] for tag in
                                    soup.find('div', 'woocommerce-product'
                                                     '-gallery').findAll(
                                        'img')]
                else:
                    picture_urls = [product['image']['src']]
                p = Product(
                    variant_name,
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
                products.append(p)
            return products
        else:
            product_container = soup.find('div', 'summary entry-summary')
            stock_container = soup.find('p', 'stock')
            if stock_container.text == 'Agotado':
                stock = 0
            else:
                stock = int(stock_container.text.split()[0])
            if soup.find('button', 'single_add_to_cart_button'):
                sku = soup.find('button', 'single_add_to_cart_button')['value']
            else:
                sku = \
                    soup.find('link', {'rel': 'shortlink'})['href'].split('=')[
                        -1]
            if product_container.find('ins'):
                price = Decimal(remove_words(
                    product_container.find('ins').
                    find('span', 'woocommerce-Price-amount amount').text))
            else:
                price = Decimal(remove_words(
                    product_container.find('span',
                                           'woocommerce-Price-amount '
                                           'amount').text))

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
