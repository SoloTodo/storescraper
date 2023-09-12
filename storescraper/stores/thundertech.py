from decimal import Decimal
import logging
from bs4 import BeautifulSoup

from storescraper.categories import (
    PROCESSOR, MOTHERBOARD, RAM,
    SOLID_STATE_DRIVE, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, MEMORY_CARD,
    USB_FLASH_DRIVE, VIDEO_CARD, POWER_SUPPLY, CPU_COOLER, MONITOR, KEYBOARD,
    MOUSE, HEADPHONES, STEREO_SYSTEM, KEYBOARD_MOUSE_COMBO, PRINTER, NOTEBOOK,
    TABLET, WEARABLE, ALL_IN_ONE)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Thundertech(StoreWithUrlExtensions):
    url_extensions = [
        ['procesador', PROCESSOR],
        ['placa-madre', MOTHERBOARD],
        ['memorias-ram', RAM],
        ['disco-estado-solido', SOLID_STATE_DRIVE],
        ['disco-duro-notebook', STORAGE_DRIVE],
        ['disco-duro-pcs', STORAGE_DRIVE],
        ['nas', SOLID_STATE_DRIVE],
        ['discos-portatiles', EXTERNAL_STORAGE_DRIVE],
        ['discos-sobremesa', EXTERNAL_STORAGE_DRIVE],
        ['memorias-flash', MEMORY_CARD],
        ['pendrive', USB_FLASH_DRIVE],
        ['tarjeta-de-video', VIDEO_CARD],
        ['componentes/fuentes-de-poder', POWER_SUPPLY],
        ['componentes/disipadores', CPU_COOLER],
        ['monitores', MONITOR],
        ['teclados', KEYBOARD],
        ['mouse', MOUSE],
        ['audifonos', HEADPHONES],
        ['parlantes', STEREO_SYSTEM],
        ['kit-perifericos', KEYBOARD_MOUSE_COMBO],
        ['impresoras', PRINTER],
        ['mac', NOTEBOOK],
        ['macbook', NOTEBOOK],
        ['ipad', TABLET],
        ['watch', WEARABLE],
        ['accesorios-1', KEYBOARD],
        ['todo-en-uno', ALL_IN_ONE],
        ['portatiles', NOTEBOOK],
        ['tableta', TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('Page overflow: ' + url_extension)
            url_webpage = 'https://www.thundertech.cl/{}?page={}'.format(
                url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('div', 'product-block')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = ('https://www.thundertech.cl' +
                               container.find('a')['href'])
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-heading__title').text.strip()
        key = soup.find('meta', {'property': 'og:id'})['content']
        # TODO: check for una unavailable product in the future
        stock = -1

        discount_price_tag = soup.find(
            'h2', 'product-heading__pricing--has-discount')

        if discount_price_tag:
            price = Decimal(remove_words(discount_price_tag.find(
                'span',).text))
        else:
            price = Decimal(remove_words(soup.find(
                'h2', 'product-heading__pricing').text))

        sku_tag = soup.find('span', 'product-heading__detail--sku')
        if sku_tag:
            sku = sku_tag.text.split('SKU: ')[1]
        else:
            sku = None

        picture_urls = [x['data-src'] for x in
                        soup.findAll('img', 'product-gallery__image')]

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
            picture_urls=picture_urls,
            part_number=sku
        )
        return [p]
