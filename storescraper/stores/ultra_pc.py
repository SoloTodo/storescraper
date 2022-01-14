import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, TABLET, CELL, \
    SOLID_STATE_DRIVE, PROCESSOR, RAM, KEYBOARD_MOUSE_COMBO, PRINTER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class UltraPc(Store):

    @classmethod
    def categories(cls):
        return [
            ALL_IN_ONE,
            NOTEBOOK,
            TABLET,
            CELL,
            SOLID_STATE_DRIVE,
            PROCESSOR,
            RAM,
            KEYBOARD_MOUSE_COMBO,
            PRINTER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-para-pc/kits', KEYBOARD_MOUSE_COMBO],
            ['computadores-de-escritorio/all-in-one', ALL_IN_ONE],
            ['impresoras', PRINTER],
            ['laptop', NOTEBOOK],
            ['tablets-e-ipads', TABLET],
            ['smartphones', CELL],
            ['almacenamiento-solido', SOLID_STATE_DRIVE],
            ['procesadores', PROCESSOR],
            ['memorias-ram', RAM],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.ultrapc.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-outer')

                if not product_containers or soup.find('div', 'info-404'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers:
                    product_url = \
                        container.find('a', 'woocommerce-LoopProduct-link')[
                            'href']
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
        sku = soup.find('link', {'type': 'application/json'})['href'].split(
            '/')[-1]
        if soup.find('span', 'electro-stock-availability').find('p', 'stock'):
            stock = -1
        else:
            stock = 0
        iva = Decimal('1.19')
        normal_price = (iva * Decimal(
            remove_words(soup.find('div', 'precios_iva').text.split()[0]))). \
            quantize(0)
        offer_price = (iva * Decimal(remove_words(
            soup.find('p', 'price').find('span', 'electro-price').find(
                'bdi').text))).quantize(0)
        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll(
            'img')]
        condition_text = soup.find(
            'span', 'condicion_item_ultrapc').text.strip()
        if condition_text == 'NUEVO':
            condition = 'https://schema.org/NewCondition'
        else:
            condition = 'https://schema.org/RefurbishedCondition'

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
            picture_urls=picture_urls,
            condition=condition
        )
        return [p]
