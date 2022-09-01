import json
import logging
import re

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from .mercado_libre_chile import MercadoLibreChile
from storescraper.utils import session_with_proxy
from storescraper.categories import CELL, HEADPHONES, MOUSE, WEARABLE, \
    STEREO_SYSTEM, TABLET, MONITOR, GAMING_CHAIR, KEYBOARD, POWER_SUPPLY, \
    COMPUTER_CASE


class MobileHut(MercadoLibreChile):
    @classmethod
    def categories(cls):
        return [
            CELL,
            HEADPHONES,
            STEREO_SYSTEM,
            MOUSE,
            WEARABLE,
            TABLET,
            KEYBOARD,
            POWER_SUPPLY,
            GAMING_CHAIR,
            MONITOR,
            COMPUTER_CASE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['computacion/monitores-accesorios/monitores/accesorios', MONITOR],
            ['computacion/accesorios-pc-gaming/audifonos/accesorios',
             HEADPHONES],
            ['computacion/accesorios-pc-gaming/sillas-gamer/accesorios',
             GAMING_CHAIR],
            ['electronica-audio-video/audio/accesorios', STEREO_SYSTEM],
            ['electronica-audio-video/audio/audio-portatil-accesorios',
             STEREO_SYSTEM],
            ['celulares-telefonia/smartwatches-accesorios/accesorios',
             WEARABLE],
            ['computacion/perifericos-accesorios/mouses/computacion', MOUSE],
            ['computacion/perifericos-accesorios/teclados/computacion',
             KEYBOARD],
            ['computacion/monitores-accesorios/monitores/computacion',
             MONITOR],
            ['computacion/componentes-pc/fuentes-alimentacion', POWER_SUPPLY],
            ['computacion/componentes-pc/gabinetes-soportes-pc',
             COMPUTER_CASE],
            ['computacion/perifericos-accesorios/teclados/gaming', KEYBOARD],
            ['computacion/perifericos-accesorios/mouses/gaming', MOUSE],
            ['computacion/accesorios-pc-gaming/audifonos/gaming', HEADPHONES],
            ['computacion/accesorios-pc-gaming/sillas-gamer/gaming',
             GAMING_CHAIR],
            ['computacion/tablets-accesorios/tablets', TABLET],
            ['celulares-telefonia/celulares-smartphones/smartphones', CELL],
            ['smartwatch', WEARABLE],
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
                index = str(50 * (page - 1) + 1)
                url_webpage = 'https://www.mobilehut.cl/listado/' \
                              '{}/_Desde_{}_NoIndex_True'.format(url_extension,
                                                                 index)
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
