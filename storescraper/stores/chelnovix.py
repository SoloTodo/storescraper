from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import CASE_FAN, COMPUTER_CASE, CPU_COOLER, \
    GAMING_CHAIR, KEYBOARD, MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, \
    POWER_SUPPLY, PRINTER, PROCESSOR, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class Chelnovix(Store):
    @classmethod
    def categories(cls):
        return [
            PRINTER,
            MONITOR,
            MOTHERBOARD,
            VIDEO_CARD,
            KEYBOARD,
            NOTEBOOK,
            POWER_SUPPLY,
            COMPUTER_CASE,
            CPU_COOLER,
            CASE_FAN,
            PROCESSOR,
            GAMING_CHAIR,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['impresoras', PRINTER],
            ['monitores', MONITOR],
            ['partes-y-piezas/placa-madre', MOTHERBOARD],
            ['tarjeta-de-video', VIDEO_CARD],
            ['computadores/notebook', NOTEBOOK],
            ['partes-y-piezas/fuentes', POWER_SUPPLY],
            ['partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/refrigeracion-liquida', CPU_COOLER],
            ['partes-y-piezas/disipador', CASE_FAN],
            ['partes-y-piezas/procesadores', PROCESSOR],
            ['accesorios-gamer/silla-gamer', GAMING_CHAIR],
            ['accesorios-gamer/teclados-gamer', KEYBOARD],
            ['accesorios-gamer/mouse-gamer', MOUSE],
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
                url_webpage = 'https://chelnovix.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a', 'woocommerce-Loop'
                                                      'Product-link')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})[
            'href'].split('=')[-1]
        name = soup.find('h1', 'product_title').text.strip()

        input_qty = soup.find('input', 'qty')
        stock = 0
        if input_qty:
            if 'max' in input_qty.attrs and input_qty['max']:
                stock = int(input_qty['max'])
            else:
                stock = -1

        span_sku = soup.find('span', 'sku')
        sku = None
        if span_sku:
            sku = span_sku.text.strip()

        span_price = soup.find('p', 'price').findAll(
            'span', 'woocommerce-Price-amount')
        if len(span_price) == 0:
            return []
        elif len(span_price) > 1:
            price = Decimal(remove_words(span_price[1].text))
        else:
            price = Decimal(remove_words(span_price[0].text))

        picture_urls = []
        picture_container = soup.find(
            'div', 'woocommerce-product-gallery__image')
        for i in picture_container.findAll('img'):
            picture_urls.append(i['src'])

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
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
