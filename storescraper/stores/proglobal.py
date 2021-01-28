import logging
from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.store import Store
from storescraper.product import Product
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import CELL, WEARABLE, PROJECTOR, MEMORY_CARD, \
    USB_FLASH_DRIVE, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, HEADPHONES, \
    MOUSE, KEYBOARD, COMPUTER_CASE, RAM, POWER_SUPPLY, MONITOR, \
    STEREO_SYSTEM, MOTHERBOARD, PROCESSOR, VIDEO_CARD, CPU_COOLER, GAMING_CHAIR


class Proglobal(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            WEARABLE,
            PROJECTOR,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            COMPUTER_CASE,
            RAM,
            POWER_SUPPLY,
            MONITOR,
            STEREO_SYSTEM,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            CPU_COOLER,
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['celulares/smartphone', CELL],
            ['celulares/pulseras-inteligentes', WEARABLE],
            ['computacion-y-gamer/proyectores/proyectores-led', PROJECTOR],
            ['computacion-y-gamer/almacenamiento/microsd-alta-velocidad',
             MEMORY_CARD],
            ['computacion-y-gamer/almacenamiento/tarjetas-sd', MEMORY_CARD],
            ['computacion-y-gamer/almacenamiento/pendrives', USB_FLASH_DRIVE],
            ['computacion-y-gamer/almacenamiento/discos-duros',
             EXTERNAL_STORAGE_DRIVE],
            ['computacion-y-gamer/gamers/audifonos', HEADPHONES],
            ['computacion-y-gamer/gamers/mouse', MOUSE],
            ['computacion-y-gamer/gamers/teclados', KEYBOARD],
            ['computacion-y-gamer/gamers/gabinete-para-pc', COMPUTER_CASE],
            ['computacion-y-gamer/gamers/memoria-ram', RAM],
            ['computacion-y-gamer/gamers/fuentes-de-poder', POWER_SUPPLY],
            ['computacion-y-gamer/gamers/monitores', MONITOR],
            ['camaras-audio-video/audio/audio-alta-fidelidad',
             STEREO_SYSTEM],
            ['camaras-audio-video/audio/audifonos-inalambricos', HEADPHONES],
            ['camaras-audio-video/audio/audifonos-alambricos', HEADPHONES],
            ['camaras-audio-video/audio/parlantes', STEREO_SYSTEM],
            ['computacion-y-gamer/hardware-pc-gamer/placas-madre',
             MOTHERBOARD],
            ['computacion-y-gamer/hardware-pc-gamer/procesadores',
             PROCESSOR],
            ['computacion-y-gamer/hardware-pc-gamer/tarjetas-de-video',
             VIDEO_CARD],
            ['computacion-y-gamer/hardware-pc-gamer/memorias-ram',
             RAM],
            ['computacion-y-gamer/hardware-pc-gamer/fuentes-de-poder',
             POWER_SUPPLY],
            ['computacion-y-gamer/hardware-pc-gamer/gabinetes-para-pc',
             COMPUTER_CASE],
            ['computacion-y-gamer/hardware-pc-gamer/'
             'ventiladores-y-enfriadores', CPU_COOLER],
            ['computacion-y-gamer/gamers/sillas-y-alfombras-gamer',
             GAMING_CHAIR]
        ]

        session = session_with_proxy(extra_args)
        base_url = 'https://www.proglobal.cl/{}'
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                url = 'https://proglobal.cl/c/{}/pagina-{}' \
                    .format(category_path, page)
                print(url)

                response = session.get(url)

                # Deactivated category
                if response.url != url:
                    logging.warning('Deactivated category: ' + url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll(
                    'div', 'producto-carrusel-home')

                if not len(product_containers):
                    if page == 1:
                        logging.warning('Empty category: {}'.format(url))
                    break

                for container in product_containers:
                    product_urls.append(
                        base_url.format(container.find('a')['href']))

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url)
        soup = BeautifulSoup(data.text, 'html.parser')

        name = soup.find('h3').text
        sku = soup.find('p', 'sku').text.replace('SKU:', '').strip()

        price_container = soup.find('span', 'precio-ficha')

        if not price_container:
            price_container = soup.find('span', 'tachado-efectivo')

        if not price_container:
            return []

        price = Decimal(price_container
                        .text.replace('Precio final:', '')
                        .replace('$', '')
                        .replace('.-', '')
                        .replace('.', '').strip())

        pictures_containers = soup.findAll('a', 'miniatura_galeria')
        base_url = 'https://www.proglobal.cl/{}'
        picture_urls = []

        for picture in pictures_containers:
            picture_url = base_url.format(picture['data-zoom'])
            picture_urls.append(picture_url)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'descripcion'})))

        if 'preventa' in description.lower():
            stock = 0
        elif soup.find('a', 'notificar_stock'):
            stock = 0
        else:
            stock = -1

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
