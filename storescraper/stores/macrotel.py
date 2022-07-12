from decimal import Decimal
import json
import logging

from bs4 import BeautifulSoup
from storescraper.categories import GAMING_CHAIR, GAMING_DESK, HEADPHONES, \
    KEYBOARD, MEMORY_CARD, MICROPHONE, MOUSE, RAM, STEREO_SYSTEM, TABLET, \
    USB_FLASH_DRIVE, VIDEO_CARD, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Macrotel(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MICROPHONE,
            VIDEO_CARD,
            RAM,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            GAMING_DESK,
            GAMING_CHAIR,
            MOUSE,
            KEYBOARD,
            TABLET,
            STEREO_SYSTEM,
            VIDEO_GAME_CONSOLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audio-y-video/audifonos', HEADPHONES],
            ['audio-y-video/parlantes', STEREO_SYSTEM],
            ['audio-y-video/microfonos', MICROPHONE],
            ['computacion/componentes/tarjetas-de-video', VIDEO_CARD],
            ['computacion/almacenamiento/memoria-ram', RAM],
            ['computacion/almacenamiento/pendrives', USB_FLASH_DRIVE],
            ['computacion/almacenamiento/tarjetas', MEMORY_CARD],
            ['computacion/muebles-de-computacion/escritorios', GAMING_DESK],
            ['computacion/muebles-de-computacion/sillas', GAMING_CHAIR],
            ['computacion/perifericos/mouse', MOUSE],
            ['computacion/perifericos/teclados', KEYBOARD],
            ['computacion/tablets-y-accesorios/tablets', TABLET],
            ['computacion/perifericos/parlantes', STEREO_SYSTEM],
            ['aire-libre-y-diversion/consolas-y-videojuegos/consolas',
                VIDEO_GAME_CONSOLE],
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
                url_webpage = 'https://www.macrotel.cl/{}' \
                              '?page={}'.format(url_extension, page)
                retries = 3
                while retries:
                    try:
                        data = session.get(url_webpage).text
                        soup = BeautifulSoup(data, 'html.parser')
                        json_data = json.loads(soup.findAll(
                            'script', {'type': 'application/ld+json'})[1].text)
                        break
                    except Exception as e:
                        if retries:
                            retries -= 1
                        else:
                            raise

                item_list = json_data['itemListElement']
                if len(item_list) == 0:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                else:
                    for i in item_list:
                        product_urls.append(i['item']['@id'])
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_tags = soup.findAll('script', {'type': 'application/ld+json'})

        if not json_tags:
            return []

        json_data = json.loads(json_tags[0].text)
        name = json_data['name']
        sku = str(json_data['sku'])
        price = Decimal(json_data['offers']['offers'][0]['price'])
        description = json_data['description']

        if 'preventa' in name.lower():
            stock = 0
        elif soup.find('input', 'vtex-numeric-stepper__input'):
            stock = -1
        else:
            stock = 0

        picture_urls = []
        image_container = soup.find('div', 'swiper-container')
        for i in image_container.findAll('img'):
            picture_urls.append(i['src'])

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
            picture_urls=picture_urls,
            description=description
        )
        return [p]
