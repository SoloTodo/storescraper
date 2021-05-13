import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STORAGE_DRIVE, USB_FLASH_DRIVE, \
    SOLID_STATE_DRIVE, HEADPHONES, STEREO_SYSTEM, KEYBOARD, MOUSE, \
    GAMING_CHAIR, KEYBOARD_MOUSE_COMBO
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class TecnoStoreChile(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            SOLID_STATE_DRIVE,
            HEADPHONES,
            STEREO_SYSTEM,
            KEYBOARD,
            MOUSE,
            GAMING_CHAIR,
            KEYBOARD_MOUSE_COMBO,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['393-hdd', STORAGE_DRIVE],
            ['391-pendrives', USB_FLASH_DRIVE],
            ['392-ssd', SOLID_STATE_DRIVE],
            ['394-m2', SOLID_STATE_DRIVE],
            ['387-audifonos', HEADPHONES],
            ['388-parlantes', STEREO_SYSTEM],
            ['389-equipos-de-audio', STEREO_SYSTEM],
            ['401-audifonos-gamer', STEREO_SYSTEM],
            ['399-teclados', KEYBOARD],
            ['396-teclados', KEYBOARD],
            ['398-mouse', MOUSE],
            ['395-mouse', MOUSE],
            ['403-sillas', GAMING_CHAIR],
            ['397-conjuntos', KEYBOARD_MOUSE_COMBO],
            ['400-conjuntos', KEYBOARD_MOUSE_COMBO],
            ['397-conjuntos', KEYBOARD_MOUSE_COMBO],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            do = True
            while do:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://tecnostorechilespa.cl/{}#/page-{}' \
                    .format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'products grid')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll(
                        'div', 'product-wrapper'):
                    product_url = container.find('a')['href']
                    if product_url in product_urls:
                        do = False
                        break
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h3', 'title-pro-detalle').text
        sku = soup.find('input', {'name': 'id_product'})['value']
        if soup.find('label', 'etiqueta-nodisponible'):
            stock = 0
        else:
            stock = -1
        normal_price = Decimal(round(int(remove_words(
            soup.find('div', 'price').find('span', 'price').text)) * 1.04))
        offer_price = Decimal(
            remove_words(soup.find('div', 'price').find('span', 'price').text))
        picture_url = [tag['src'] for tag in
                       soup.find('div', {'id': 'views_block'}).findAll('img')]
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
            picture_urls=picture_url
        )
        return [p]
