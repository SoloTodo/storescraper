import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PROCESSOR, MOTHERBOARD, VIDEO_CARD, RAM, \
    SOLID_STATE_DRIVE, COMPUTER_CASE, MONITOR, NOTEBOOK, MOUSE, \
    POWER_SUPPLY, CPU_COOLER, HEADPHONES, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class MegaBytes(StoreWithUrlExtensions):
    preferred_products_for_url_concurrency = 3

    url_extensions = [
        ['accesorios/mas-accesorios', MOUSE],
        ['accesorios/mouse-teclados', MOUSE],
        ['componentes-pc/almacenamiento', SOLID_STATE_DRIVE],
        ['componentes-pc/fuentes-de-poder', POWER_SUPPLY],
        ['componentes-pc/gabinetes', COMPUTER_CASE],
        ['componentes-pc/memorias', RAM],
        ['componentes-pc/placa-madre', MOTHERBOARD],
        ['componentes-pc/procesador', PROCESSOR],
        ['componentes-pc/tarjetas-graficas', VIDEO_CARD],
        ['componentes-pc/ventilacion', CPU_COOLER],
        ['monitores', MONITOR],
        ['notebooks', NOTEBOOK],
        ['accesorios/audifonos-headsets', HEADPHONES],
        ['otros', VIDEO_GAME_CONSOLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'SoloTodoBot'
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://megabytes.cl/categoria-producto/{}/' \
                          'page/{}/'.format(url_extension, page)
            print(url_webpage)
            data = session.get(url_webpage)

            if data.status_code == 404:
                if page == 1:
                    # raise Exception(url_webpage)
                    logging.warning('Empty category: ' + url_extension)
                break
            soup = BeautifulSoup(data.text, 'html.parser')
            product_containers = soup.findAll('div', 'product-wrapper')

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'SoloTodoBot'
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        else:
            stock = -1

        price_p = soup.find('p', 'price').text
        if not price_p:
            return []

        offer_price = Decimal(remove_words(price_p).split()[-1])

        price_container = soup.find('div', 'summary-inner').find('table')
        if price_container:
            prices = price_container.findAll(
                'span', 'woocommerce-Price-amount')
            highest_price = Decimal(0)
            for price in prices:
                p = Decimal(remove_words(price.text))
                if p > highest_price:
                    highest_price = p
            normal_price = highest_price
        else:
            normal_price = offer_price

        if normal_price < offer_price:
            normal_price = offer_price

        picture_urls = [tag['data-src'] for tag in
                        soup.find('div', 'woocommerce-product-gallery')
                            .findAll('img')
                        if 'data-src' in tag.attrs]
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
