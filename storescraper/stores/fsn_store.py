import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, MONITOR, MOUSE, KEYBOARD, \
    STORAGE_DRIVE, MOTHERBOARD, PROCESSOR, VIDEO_CARD, TELEVISION, \
    HEADPHONES, STEREO_SYSTEM, WEARABLE, NOTEBOOK, TABLET, \
    EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    RAM, PRINTER, CELL, ALL_IN_ONE, SOLID_STATE_DRIVE, MEMORY_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class FsnStore(Store):
    @classmethod
    def categories(cls):
        return [
            GAMING_CHAIR,
            MONITOR,
            MOUSE,
            KEYBOARD,
            USB_FLASH_DRIVE,
            STORAGE_DRIVE,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            TELEVISION,
            HEADPHONES,
            STEREO_SYSTEM,
            WEARABLE,
            NOTEBOOK,
            TABLET,
            EXTERNAL_STORAGE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            PRINTER,
            CELL,
            ALL_IN_ONE,
            SOLID_STATE_DRIVE,
            MEMORY_CARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['celulares', CELL],
            ['tecnologia/computadores-de-escritorio', ALL_IN_ONE],
            ['computadores-portatilestablets-1/notebook', NOTEBOOK],
            ['computadores-portatilestablets-1/ipad-tablet', TABLET],
            ['tecnologia/discos-duros/disco-duro-externo',
             EXTERNAL_STORAGE_DRIVE],
            ['tecnologia/discos-duros/disco-duro-interno', STORAGE_DRIVE],
            ['otros', STORAGE_DRIVE],
            ['tecnologia/fuentes-de-poder', POWER_SUPPLY],
            ['tecnologia/gabinetes-de-pcs', COMPUTER_CASE],
            ['memoria-ram', RAM],
            ['tecnologia/memorias/memoria-flash', USB_FLASH_DRIVE],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['teclado', KEYBOARD],
            ['otros-mouse-y-teclado', MOUSE],
            ['tecnologia/pendrives', USB_FLASH_DRIVE],
            ['tecnologia/placa-madre', MOTHERBOARD],
            ['tecnologia/procesadores-amd', PROCESSOR],
            ['tecnologia/procesadores-intel', PROCESSOR],
            ['tarjetas-gr-ficas', VIDEO_CARD],
            ['tecnologia/televisores', TELEVISION],
            ['unidad-ssd', SOLID_STATE_DRIVE],
            ['tecnologia/sillas', GAMING_CHAIR],
            ['audifonos', HEADPHONES],
            ['fsn-play/parlantes', STEREO_SYSTEM],
            ['fsn-play/relojes-trackers-de-actividad', WEARABLE],
            ['play', MEMORY_CARD],
            ['impresoras', PRINTER]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://www.fsnstore.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'four shop columns')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.fsnstore.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1').text
        key = soup.find('form', {'id': 'addtocart'})['action'].split('/')[-1]
        sku = soup.find('h2', {'id': 'product-sku'}).text
        stock_container = soup.find('div', 'product_stock_info')
        stock = 0
        if stock_container:
            stock = int(stock_container.findAll('span')[-1].text)
        price = Decimal(
            remove_words(soup.find('span', {'id': 'product-price'}).text))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'slider-padding').findAll('img')]
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
            part_number=sku,
            picture_urls=picture_urls,

        )
        return [p]
