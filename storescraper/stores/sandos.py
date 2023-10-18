import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TABLET, HEADPHONES, MOUSE, KEYBOARD, \
    GAMING_CHAIR, MONITOR, MOTHERBOARD, RAM, POWER_SUPPLY, CPU_COOLER, \
    COMPUTER_CASE, PROCESSOR, SOLID_STATE_DRIVE, NOTEBOOK, VIDEO_CARD
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Sandos(StoreWithUrlExtensions):
    url_extensions = [
        ['tablet', TABLET],
        ['almacenamiento', SOLID_STATE_DRIVE],
        ['cooler', CPU_COOLER],
        ['fuentes-de-poder', POWER_SUPPLY],
        ['gabinetes', COMPUTER_CASE],
        ['memorias-ram', RAM],
        ['placas-madre', MOTHERBOARD],
        ['procesadores', PROCESSOR],
        ['tarjetas-de-video', VIDEO_CARD],
        ['monitores', MONITOR],
        ['audifonos', HEADPHONES],
        ['mouse', MOUSE],
        ['teclados', KEYBOARD],
        ['sillas-gamer', GAMING_CHAIR],
        ['notebooks', NOTEBOOK],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://sandos.cl/product-category' \
                          '/{}/page/{}/'.format(url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            if soup.find('body', 'error404'):
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break

            product_containers = soup.find(
                'div', 'site-content').findAll('div', 'product')

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
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
            -1]

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        description = product_data['description']
        sku = str(product_data['sku'])
        offer_price = Decimal(product_data['offers'][0]['price'])

        price_table = soup.find('table', {'id': 'precio_tabla'})
        price_spans = price_table.findAll('span', 'amount')
        if len(price_spans) > 1:
            normal_price = Decimal(remove_words(price_spans[-1].text))
        else:
            normal_price = offer_price

        stock_p = soup.find('p', 'in-stock')
        if stock_p:
            stock = int(stock_p.text.split(' ')[0])
        else:
            stock = -1

        picture_urls = [product_data['image']]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
