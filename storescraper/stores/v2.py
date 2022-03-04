import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MONITOR, MOUSE, RAM, TABLET, \
    KEYBOARD, SOLID_STATE_DRIVE, HEADPHONES, VIDEO_CARD, CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class V2(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MONITOR,
            MOUSE,
            RAM,
            TABLET,
            KEYBOARD,
            SOLID_STATE_DRIVE,
            HEADPHONES,
            VIDEO_CARD,
            CELL,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['3-notebooks', NOTEBOOK],
            ['14-monitores', MONITOR],
            ['28-mouse', MOUSE],
            ['35-memorias-ram', RAM],
            ['29-tablets', TABLET],
            ['22-teclados', KEYBOARD],
            ['25-discos-ssd', SOLID_STATE_DRIVE],
            ['36-headsets', HEADPHONES],
            ['39-tarjetas-de-video', VIDEO_CARD],
            ['40-almacenamiento', SOLID_STATE_DRIVE],
            ['44-audifonos', HEADPHONES],
            ['46-celulares', CELL],
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
                url_webpage = 'https://v2.cl/{}?page={}'.format(url_extension,
                                                                page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', {
                    'itemprop': 'itemListElement'})
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
        json_container = json.loads(
            soup.find('div', {'id': 'product-details'})['data-product'])
        name = json_container['name']
        sku = str(json_container['id'])
        description = soup.find('div', 'product-description')
        if description.find('strong') and 'Disponible desde' in description \
                .find('strong').text:
            stock = 0
        else:
            stock = json_container['quantity']

        if soup.find('meta', {'property': 'product:price:condition'})[
                'content'] == 'new':
            condition = 'https://schema.org/NewCondition'
        else:
            condition = 'https://schema.org/RefurbishedCondition'

        price = Decimal(json_container['price_amount'])
        picture_urls = [tag['src'] for tag in
                        soup.find('ul', 'product-images').findAll('img')]
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
            picture_urls=picture_urls,
            condition=condition
        )
        return [p]
