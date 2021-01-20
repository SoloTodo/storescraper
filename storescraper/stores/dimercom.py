import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper.categories import STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    MOTHERBOARD, PROCESSOR, RAM, VIDEO_CARD, POWER_SUPPLY, COMPUTER_CASE, \
    MOUSE, KEYBOARD, MONITOR, CPU_COOLER, KEYBOARD_MOUSE_COMBO


class Dimercom(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            MOTHERBOARD,
            PROCESSOR,
            RAM,
            VIDEO_CARD,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOUSE,
            KEYBOARD,
            MONITOR,
            CPU_COOLER,
            KEYBOARD_MOUSE_COMBO
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-6/componentes-unidades-ssd-58', SOLID_STATE_DRIVE],
            ['componentes-6/componentes-tarjetas-madre-116', MOTHERBOARD],
            ['componentes-6/componentes-procesadores-194', PROCESSOR],
            # Ram Desktop
            ['componentes-6/componentes-ram-para-desktop-118', RAM],
            # Ram Notebook
            ['componentes-6/componentes-ram-para-laptop-163', RAM],
            # Overflows on nvidia cards
            # ['componentes-6/componentes-tarjetas-de-video-115', VIDEO_CARD],
            ['energia-10/energia-fuentes-de-poder-137', POWER_SUPPLY],
            ['gabinetes-y-enfriamiento-26/gabinetes-y-enfriamiento'
             '-gabinetes-149', COMPUTER_CASE],
            # Overflows on nvidia cards
            # ['teclados-mouses-1/teclados-mouses-mouse-33', MOUSE],
            ['teclados-mouses-1/teclados-mouses-teclados-32', KEYBOARD],
            ['monitores-15', MONITOR],
            ['gabinetes-y-enfriamiento-26/gabinetes-y-enfriamiento'
             '-enfriamiento-liquido-148', CPU_COOLER],
            ['gabinetes-y-enfriamiento-26/gabinetes-y-enfriamiento'
             '-ventiladores-150', CPU_COOLER],
            ['teclados-mouses-1/teclados-mouses-kit-76', KEYBOARD_MOUSE_COMBO]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1

            while True:
                if page > 20:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.dimercom.mx/product-category/' \
                              '{}/page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_container = soup.find('ul',
                                              {'data-toggle': 'shop-products'})
                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for product in product_container.findAll('li'):
                    product_url = product.find('a', 'woocommerce-LoopProduct'
                                                    '-link')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_container = soup.find('div', 'single-product-wrapper')
        name = product_container.find('h1', 'product_title').text
        sku = product_container.find('a', 'add_to_wishlist')['data-product-id']
        if product_container.find('p', 'stock in-stock'):
            stock = int(product_container.find(
                'p', 'stock in-stock').text.split()[0].strip())
        else:
            stock = 0
        price = Decimal(product_container.find('span',
                                               'woocommerce-Price-amount')
                        .text.replace('$', '').replace(',', ''))
        picture_urls = [product_container.find('img', 'wp-post-image')['src']]

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
            'MXN',
            sku=sku,
            picture_urls=picture_urls,
        )

        return [p]
