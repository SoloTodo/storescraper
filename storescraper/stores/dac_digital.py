import logging
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import KEYBOARD, VIDEO_CARD
from storescraper.stores.mercado_libre_chile import MercadoLibreChile
from storescraper.utils import session_with_proxy


class DacDigital(MercadoLibreChile):
    @classmethod
    def categories(cls):
        return [
            KEYBOARD,
            VIDEO_CARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['perifericos-pc', KEYBOARD],
            ['componentes-pc', VIDEO_CARD],
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
                index = str(50*(page - 1) + 1)
                url_webpage = 'https://www.dacdigital.cl/listado/' \
                    '{}/_Desde_{}_NoIndex_True'.format(url_extension, index)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'li', 'ui-search-layout__item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find(
                        'a',
                        'ui-search-link')['href'].split('#')[0].split('?')[0]
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        price = Decimal(soup.find('meta', {'itemprop': 'price'})['content'])

        products = super().products_for_url(
            url, category=category, extra_args=extra_args)

        for product in products:
            product.url = url
            product.discovery_url = url
            product.offer_price = price
            product.normal_price = price
            product.seller = None

        return products
