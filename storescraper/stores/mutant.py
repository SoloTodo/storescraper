from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import COMPUTER_CASE, CPU_COOLER, KEYBOARD, \
    MONITOR, MOTHERBOARD, MOUSE, POWER_SUPPLY, SOLID_STATE_DRIVE, VIDEO_CARD, \
    PROCESSOR, RAM, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, remove_words, \
    session_with_proxy


class Mutant(StoreWithUrlExtensions):
    url_extensions = [
        ['tarjeta-video', VIDEO_CARD],
        ['fuente-de-poder', POWER_SUPPLY],
        ['placa-madre', MOTHERBOARD],
        ['discos-ssd', SOLID_STATE_DRIVE],
        ['sistema-refrigeracion', CPU_COOLER],
        ['gabinetes', COMPUTER_CASE],
        ['monitor', MONITOR],
        ['mouse', MOUSE],
        ['cpu', PROCESSOR],
        ['memoria-ram', RAM],
        ['teclados-armados', KEYBOARD],
        ['audifonos', HEADPHONES],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        url_webpage = 'https://www.mutant.cl/{}/'.format(url_extension)
        print(url_webpage)
        data = session.get(url_webpage).text
        soup = BeautifulSoup(data, 'html.parser')
        product_containers = soup.findAll('div', 'jet-woo-products__item')

        if not product_containers:
            logging.warning('Empty category: ' + url_extension)

        for container in product_containers:
            product_url = container.find('a')['href']
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        short_description_tag = soup.find(
            'div', 'woocommerce-product-details__short-description')
        is_reserva = 'RESERVA' in str(short_description_tag).upper()

        picture_container = soup.find(
            'div', 'woocommerce-product-gallery__wrapper')
        picture_urls = []
        for a in picture_container.findAll('a'):
            if a['href'] != '':
                picture_urls.append(a['href'])

        variations = soup.find('form', 'variations_form')
        if variations:
            products = []
            variants = json.loads(variations['data-product_variations'])
            for v in variants:
                key = str(v['variation_id'])
                attr = ' '.join(list(v['attributes'].values()))
                variant_name = '{} - {}'.format(name, attr)
                sku = v['sku']
                price = Decimal(v['display_price'])

                if is_reserva:
                    stock = 0
                elif v['max_qty'] != "":
                    stock = v['max_qty']
                else:
                    stock = 0

                p = Product(
                    variant_name,
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
                    picture_urls=picture_urls,
                    description=description
                )
                products.append(p)

            return products
        else:
            key = soup.find('link', {'rel': 'shortlink'})[
                'href'].split('p=')[1]

            price_container = soup.find('p', 'price')
            price = Decimal(remove_words(
                price_container.findAll('span', 'amount')[-1].text))

            stock_container = soup.find('p', 'stock in-stock')
            if is_reserva:
                stock = 0
            elif stock_container:
                stock = int(stock_container.text.split(' ')[0])
            elif soup.find('button', {'name': 'add-to-cart'}):
                stock = -1
            else:
                stock = 0

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
                picture_urls=picture_urls,
                description=description
            )
            return [p]
