import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, KEYBOARD, MONITOR, HEADPHONES, \
    MEMORY_CARD, CELL, SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    VIDEO_CARD, MOTHERBOARD, RAM, PROCESSOR, USB_FLASH_DRIVE, STEREO_SYSTEM, \
    TELEVISION, PRINTER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class ElectroVentas(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            MONITOR,
            HEADPHONES,
            MEMORY_CARD,
            CELL,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            VIDEO_CARD,
            MOTHERBOARD,
            RAM,
            PROCESSOR,
            USB_FLASH_DRIVE,
            PRINTER,
            STEREO_SYSTEM,
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Mouse Gamer
            ["nivel3/mouse-gaming-751", MOUSE],
            # Teclado Gamer
            ["nivel3/teclado-gamer-759", KEYBOARD],
            # Monitor Gamer
            ["nivel2/monitores-gamer-261", MONITOR],
            # Headphones Gamer
            ["nivel2/audifonos-gamer-262", HEADPHONES],
            # Normal Headphones
            ["nivel2/audifonos-158", HEADPHONES],
            ["nivel2/parlantes-180", STEREO_SYSTEM],
            ["nivel2/televisores-250", TELEVISION],
            ["nivel2/impresora-278", PRINTER],
            # NORMAL MOUSE
            ["nivel3/mouse-605", MOUSE],
            # NORMAL KEYBOARD
            ["nivel3/teclado-standard-612", KEYBOARD],
            ["nivel3/tarjetas-de-memoria-783", MEMORY_CARD],
            ["nivel3/monitores-670", MONITOR],
            # TOUCH MONITOR
            ["nivel3/monitores-touch-profesionales-728", MONITOR],
            ["nivel2/celulares-161", CELL],
            ["nivel2/unidades-de-almacenamiento-283", SOLID_STATE_DRIVE],
            ["nivel2/fuentes-de-poder-284", POWER_SUPPLY],
            ["nivel2/gabinetes-285", COMPUTER_CASE],
            ["nivel2/tarjetas-de-video-286", VIDEO_CARD],
            ["nivel2/placas-madre-282", MOTHERBOARD],
            ["nivel2/memorias-295", RAM],
            ["nivel2/procesadores-281", PROCESSOR],
            ["nivel3/pendrives-784", USB_FLASH_DRIVE]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://www.electroventas.cl/nivel/{}'.format(
                url_extension)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.find('ul', 'cuatro'). \
                findAll('li', attrs={'class': ''})
            if not product_containers:
                logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_container = soup.find('div', 'col col-7 ficha-details')

        if not product_container:
            return []
        
        name = product_container.find('div', 'pc').find('h1').text
        sku_container = next(filter(lambda x: x.text.startswith('ID'),
                                    product_container.find('div',
                                                           'pc').findAll(
                                        'li')))
        sku = sku_container.text.split()[1]
        stock = int(
            product_container.find('table', 'table').findAll('td')[3].text)
        price = Decimal(remove_words(product_container.find('div',
                                                            'price-n gray '
                                                            'precio-web-dest '
                                                            'center-content')
                                     .find('span').text.strip()))
        picture_containers = soup.find('div', 'col col-5 img ')
        if picture_containers:
            picture_urls = [tag['src'] for tag in
                            picture_containers.findAll('img')]
        else:
            picture_urls = [tag['src'] for tag in
                            soup.find('div', 'ficha').find('div',
                                                           'sp-wrap').findAll(
                                'img')]
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
            picture_urls=picture_urls
        )
        return [p]
