import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, COMPUTER_CASE, \
    MICROPHONE, SOLID_STATE_DRIVE, RAM, MONITOR, MOUSE, GAMING_CHAIR, \
    KEYBOARD, POWER_SUPPLY, MOTHERBOARD, PROCESSOR, STEREO_SYSTEM, \
    USB_FLASH_DRIVE, VIDEO_CARD, CPU_COOLER, EXTERNAL_STORAGE_DRIVE, \
    KEYBOARD_MOUSE_COMBO
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class CrazyGamesenChile(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            COMPUTER_CASE,
            SOLID_STATE_DRIVE,
            RAM,
            MONITOR,
            MOUSE,
            GAMING_CHAIR,
            KEYBOARD,
            POWER_SUPPLY,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            CPU_COOLER,
            EXTERNAL_STORAGE_DRIVE,
            MICROPHONE,
            STEREO_SYSTEM,
            USB_FLASH_DRIVE,
            KEYBOARD_MOUSE_COMBO
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['kit-gamer', KEYBOARD_MOUSE_COMBO],
            ['monitores', MONITOR],
            ['mouse-gamer', MOUSE],
            ['mouse-oficina', MOUSE],
            ['sillas-gamer', GAMING_CHAIR],
            ['teclados-gamer', KEYBOARD],
            ['teclados-oficina', KEYBOARD],
            ['audifonos-gamer', HEADPHONES],
            ['audifonos-de-musica', HEADPHONES],
            ['audifonos-home-office', HEADPHONES],
            ['microfonos-1', MICROPHONE],
            ['parlantes', STEREO_SYSTEM],
            ['discos-internos', SOLID_STATE_DRIVE],
            ['discos-externos', EXTERNAL_STORAGE_DRIVE],
            ['memorias-y-pendrive', USB_FLASH_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['memorias-ram', RAM],
            ['placas-madres', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['ventiladores-y-refrigeracion-liquida', CPU_COOLER],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.crazygamesenchile.com/collections/{}' \
                .format(url_extension)
            print(url_webpage)
            res = session.get(url_webpage)

            if res.status_code == 404:
                raise Exception('Invalid category: ' + url_extension)

            soup = BeautifulSoup(res.text, 'html.parser')
            product_containers = soup.findAll('li', 'grid__item')
            if not product_containers:
                logging.warning('Empty category: ' + url_extension)
                continue
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(
                    'https://www.crazygamesenchile.com/' + product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('input', {'name': 'id'})['value']

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        name = json_data['name']
        sku = json_data['sku']
        description = json_data['description']
        price = Decimal(str(json_data['offers'][0]['price']))

        if 'disabled' in soup.find('button', 'product-form__submit').attrs:
            stock = 0
        else:
            stock = -1

        picture_container = soup.find('ul', 'product__media-list')
        picture_urls = []
        for a in picture_container.findAll('li'):
            picture_urls.append('https:' + a.find('img')['src'])

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
            sku=key,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
