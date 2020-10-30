import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, HEADPHONES, \
    COMPUTER_CASE, RAM, PROCESSOR, VIDEO_CARD, MOTHERBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GWStore(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            HEADPHONES,
            COMPUTER_CASE,
            RAM,
            PROCESSOR,
            VIDEO_CARD,
            MOTHERBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['Almacenamiento', SOLID_STATE_DRIVE],
            ['audio-y-video/audifonos', HEADPHONES],
            ['gabinete', COMPUTER_CASE],
            ['memorias', RAM],
            ['proce', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['placas-madres', MOTHERBOARD]
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
                url_webpage = 'https://gwstore.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'shop-products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('div', 'item-col'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = str(json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)[
                      '@graph'][1]['sku'])
        stock_container = soup.find('p', 'stock')
        if stock_container:
            stock = 0 if stock_container.text.split()[0] == 'Agotado' else int(
                stock_container.text.split()[0])
        else:
            stock = -1
        price = Decimal(remove_words(soup.findAll('bdi')[-1].text))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'woocommerce-tabs').findAll('img')]
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
