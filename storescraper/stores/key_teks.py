import logging
from bs4 import BeautifulSoup
from storescraper.categories import HEADPHONES, KEYBOARD, \
    KEYBOARD_MOUSE_COMBO, MICROPHONE, MOUSE, NOTEBOOK, POWER_SUPPLY
from storescraper.stores.mercado_libre_chile import MercadoLibreChile
from storescraper.utils import session_with_proxy


class KeyTeks(MercadoLibreChile):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            KEYBOARD,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            HEADPHONES,
            MICROPHONE,
            POWER_SUPPLY,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computacion/notebooks-accesorios/notebooks', NOTEBOOK],
            ['computacion/perifericos-accesorios/teclados', KEYBOARD],
            ['computacion/perifericos-accesorios/mouses', MOUSE],
            ['mouses-teclados-controles-kits-mouse-teclado',
             KEYBOARD_MOUSE_COMBO],
            ['computacion/accesorios-pc-gaming/audifonos', HEADPHONES],
            ['computacion/accesorios-pc-gaming/microfonos', MICROPHONE],
            ['computacion/componentes-pc', POWER_SUPPLY],
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
                index = str(50*(page - 1) + 1)
                url_webpage = 'https://www.keyteks.cl/listado/' \
                    '{}/_Desde_{}_NoIndex_True'.format(url_extension, index)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'li', 'ui-search-layout__item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a', 'ui-search-link')['href']
                    product_urls.append(product_url.split('#')[0])
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super().products_for_url(
            url, category=category, extra_args=extra_args)

        for product in products:
            product.seller = None

        return products
