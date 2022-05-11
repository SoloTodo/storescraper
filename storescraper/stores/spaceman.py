import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CPU_COOLER, MOUSE, KEYBOARD, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Spaceman(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            CPU_COOLER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['home-office/mouse-ofimatica', MOUSE],
            ['home-office/teclado-ofimatica', KEYBOARD],
            ['perifericos-gaming/audifonos', HEADPHONES],
            ['perifericos-gaming/mouse', MOUSE],
            ['perifericos-gaming/teclado', KEYBOARD],
            ['refrigeracion-pc/ventiladores', CPU_COOLER],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            local_urls = []
            done = False
            while not done:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webapge = 'https://www.spaceman.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webapge)
                data = session.get(url_webapge, timeout=120).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('li', 'product'):
                    product_urls.append(container.find('a')['href'])
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        response = session.get(url, timeout=120)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text

        if soup.find('form', 'variations_form'):
            product_variants = json.loads(soup.find('form', 'variations_form')[
                'data-product_variations'])
            products = []

            if not product_variants:
                # This case https://www.spaceman.cl/producto/
                # teclado-mecanico-set-de-keycaps/
                return []

            for variant in product_variants:
                variant_name = name + ' - ' + ' '.join(
                    variant['attributes'].values())
                sku = str(variant['variation_id'])
                stock_container = BeautifulSoup(variant['availability_html'],
                                                'html.parser').find('p',
                                                                    'stock')
                if stock_container:
                    stock = int(stock_container.text.split()[0])
                elif variant['is_in_stock']:
                    stock = -1
                else:
                    stock = 0
                price = Decimal(variant['display_price'])
                picture_urls = [variant['image']['url']]
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
        add_to_cart_button = soup.find('button', {'name': 'add-to-cart'})
        json_data = json.loads(
            soup.find('script',
                      {'type': 'application/ld+json'}).text)['@graph'][-1]
        sku = str(json_data['sku'])

        if add_to_cart_button and soup.find('p', 'stock'):
            stock = int(soup.find('p', 'stock').text.split()[0])
        elif add_to_cart_button:
            stock = -1
        else:
            stock = 0

        price = Decimal(json_data['offers'][0]['price'])

        picture_urls = []
        for tag in soup.find('div', 'woocommerce-product-gallery').findAll(
                'img'):
            if 'src' in tag.attrs:
                picture_url = tag['src'].replace('-100x100', '')
                if picture_url not in picture_urls:
                    picture_urls.append(picture_url)
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
