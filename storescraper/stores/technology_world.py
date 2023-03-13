from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import AIR_CONDITIONER, ALL_IN_ONE, CELL, \
    COMPUTER_CASE, CPU_COOLER, EXTERNAL_STORAGE_DRIVE, GAMING_CHAIR, \
    HEADPHONES, KEYBOARD, KEYBOARD_MOUSE_COMBO, MEMORY_CARD, MONITOR, \
    MOTHERBOARD, MOUSE, NOTEBOOK, POWER_SUPPLY, PRINTER, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, STEREO_SYSTEM, STORAGE_DRIVE, TABLET, UPS, \
    USB_FLASH_DRIVE, VIDEO_CARD, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, \
    session_with_proxy


class TechnologyWorld(Store):
    @classmethod
    def categories(cls):
        return [
            TABLET,
            ALL_IN_ONE,
            WEARABLE,
            CELL,
            NOTEBOOK,
            MONITOR,
            PRINTER,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            EXTERNAL_STORAGE_DRIVE,
            CPU_COOLER,
            RAM,
            MOTHERBOARD,
            COMPUTER_CASE,
            VIDEO_CARD,
            PROCESSOR,
            POWER_SUPPLY,
            HEADPHONES,
            STEREO_SYSTEM,
            KEYBOARD,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            GAMING_CHAIR,
            UPS,
            AIR_CONDITIONER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['apple', NOTEBOOK],
            ['ipad', TABLET],
            ['imac-mac-mini', ALL_IN_ONE],
            ['relojes-inteligentes', WEARABLE],
            ['celulares-desbloqueados-2', CELL],
            ['notebook-1', NOTEBOOK],
            ['all-in-one-1', ALL_IN_ONE],
            ['tablets-1', TABLET],
            ['monitores-tv', MONITOR],
            ['impresoras-1', PRINTER],
            ['impresoras-de-tinta', PRINTER],
            ['impresoras-laser-1', PRINTER],
            ['impresoras-multifuncional-1', PRINTER],
            ['disco-duro-servidor', STORAGE_DRIVE],
            ['unidad-de-estado-solido-ssd', SOLID_STATE_DRIVE],
            ['disco-duro-interno', STORAGE_DRIVE],
            ['pendrive', USB_FLASH_DRIVE],
            ['tarjetas-micro-sd', MEMORY_CARD],
            ['disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
            ['fan-cooler-3', CPU_COOLER],
            ['memorias-ram-notebook', RAM],
            ['placas-madre', MOTHERBOARD],
            ['memorias-ram-pc', RAM],
            ['gabinetes-1', COMPUTER_CASE],
            ['tarjetas-de-video-1', VIDEO_CARD],
            ['procesadores-1', PROCESSOR],
            ['fuentes-de-poder-1', POWER_SUPPLY],
            ['audfonos', HEADPHONES],
            ['parlantes', STEREO_SYSTEM],
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['kit-teclados-mouse', KEYBOARD_MOUSE_COMBO],
            ['gamer', GAMING_CHAIR],
            ['ups-y-respaldos-de-energa', UPS],
            ['climatizacin', AIR_CONDITIONER],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 25:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://technologyworld.cl/productos/categori' \
                              'a/{}/pg/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-box')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    if 'producto agotado' not in \
                            container.find('div', 'price').text.lower():
                        product_url = container.find('a')['href']
                        product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('input', {'id': 'id-producto'})['value']
        name = soup.find('h4', 'name').text.strip()

        price = Decimal(remove_words(
            soup.find('div', {'id': 'precio_nuevo'}).text))

        stock = int(
            soup.find('span', {'id': 'stock-product'}).text.split(' ')[0])

        content_details = soup.find('div', 'content-detail').findAll('p')
        sku = content_details[0].text.split(' ')[-1]
        if len(content_details) > 1:
            part_number = content_details[1].text.split(' ')[-1]
        else:
            part_number = None

        content = soup.find('div', 'flat-product-content')
        description = html_to_markdown(content.find('div', 'row').text)

        picture_urls = []

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
            description=description,
            part_number=part_number
        )
        return [p]
