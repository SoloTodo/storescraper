from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, TABLET, CELL, \
    SOLID_STATE_DRIVE, PROCESSOR, RAM, KEYBOARD_MOUSE_COMBO, PRINTER, \
    VIDEO_GAME_CONSOLE
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
            PRINTER,
            VIDEO_GAME_CONSOLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['equipos-de-computo/computadores-de-escritorio-equipos-'
             'de-computo/all-in-one-computadores-de-escritorio-equipos-'
             'de-computo', ALL_IN_ONE],
            ['equipos-de-computo/laptop-equipos-de-computo', NOTEBOOK],
            ['equipos-de-computo/tablet-windows-equipos-de-computo', NOTEBOOK],
            ['accesorios/mouses-teclados', KEYBOARD_MOUSE_COMBO],
            ['tablets-e-ipads', TABLET],
            ['consolas-videojuegos', VIDEO_GAME_CONSOLE],
        ]
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://www.ultrapc.cl/categoria-producto/{}/' \
                          '?ppp=-1'.format(url_extension)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            products_container = soup.find('ul', 'products')

            if not products_container:
                continue

            for cont in products_container.findAll('div', 'product-outer'):
                product_url = \
                    cont.find('a', 'woocommerce-LoopProduct-link')[
                        'href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'type': 'application/json'})['href'].split(
            '/')[-1]
        if soup.find('span', 'electro-stock-availability').find('p', 'stock'):
            stock = -1
        else:
            stock = 0
        # iva = Decimal('1.19')
        normal_price = (Decimal(
            remove_words(soup.find('div', 'precios_iva').text.split()[0]))). \
            quantize(0)
        offer_price = (Decimal(remove_words(
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
