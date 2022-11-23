import json
import logging

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, GAMING_DESK, MICROPHONE, \
    CPU_COOLER, CELL, TABLET, WEARABLE, NOTEBOOK, ALL_IN_ONE, MEMORY_CARD, \
    RAM, EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    USB_FLASH_DRIVE, UPS, MOUSE, KEYBOARD, KEYBOARD_MOUSE_COMBO, PROCESSOR, \
    VIDEO_CARD, MOTHERBOARD, POWER_SUPPLY, COMPUTER_CASE, MONITOR, \
    TELEVISION, HEADPHONES, STEREO_SYSTEM, PRINTER, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class NotebookStore(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            TABLET,
            WEARABLE,
            NOTEBOOK,
            ALL_IN_ONE,
            MEMORY_CARD,
            RAM,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            UPS,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            PROCESSOR,
            VIDEO_CARD,
            MOTHERBOARD,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MONITOR,
            TELEVISION,
            HEADPHONES,
            STEREO_SYSTEM,
            PRINTER,
            VIDEO_GAME_CONSOLE,
            CPU_COOLER,
            GAMING_CHAIR,
            GAMING_DESK,
            MICROPHONE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Portabilidad
            ['tecnologia-portatil/celulares/celulares-desbloqueados', CELL],
            ['tecnologia-portatil/celulares/tableta-2', TABLET],
            ['tecnologia-portatil/relojes-y-trackers/trackers-de-actividad',
             WEARABLE],
            # Equipos
            ['equipos/computadores-1/portatiles-1', NOTEBOOK],
            ['equipos/computadores-1/ultrabooks', NOTEBOOK],
            ['equipos/computadores-1/todo-en-uno', ALL_IN_ONE],
            ['equipos/memorias/tarjetas-de-memoria-flash', MEMORY_CARD],
            ['equipos/memorias/ram-para-notebooks', RAM],
            ['equipos/memorias/ram-para-pc-y-servidores', RAM],
            ['equipos/alm/discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['equipos/alm/discos-duros-internos', STORAGE_DRIVE],
            ['equipos/alm/discos-de-estado-solido', SOLID_STATE_DRIVE],
            ['equipos/alm/unidades-flash-usb', USB_FLASH_DRIVE],
            ['equipos/seguridad/ups-respaldo-de-energia', UPS],
            ['equipos/perifericos/ratones', MOUSE],
            ['equipos/perifericos/teclados-y-teclados-de-numeros', KEYBOARD],
            ['equipos/perifericos/combos-de-teclado-y-raton',
             KEYBOARD_MOUSE_COMBO],
            ['equipos/muebles/sillas', GAMING_CHAIR],
            ['equipos/muebles/escritorios', GAMING_DESK],
            ['equipos/componentes-informaticos/procesadores', PROCESSOR],
            ['equipos/componentes-informaticos/tarjetas-de-video', VIDEO_CARD],
            ['equipos/componentes-informaticos/tarjetas-madre-placas-madre',
             MOTHERBOARD],
            ['equipos/componentes-informaticos/fuentes-de-poder',
             POWER_SUPPLY],
            ['equipos/componentes-informaticos/cajas-gabinetes',
             COMPUTER_CASE],
            ['equipos/componentes-informaticos/'
             'ventiladores-y-sistemas-de-enfriamiento', CPU_COOLER],
            # Audio Video y Foto
            ['audio-y-video/monitores-proyectores/monitores', MONITOR],
            ['audio-y-video/monitores-proyectores/televisores', TELEVISION],
            ['audio-y-video/audio-y-video/auriculares', HEADPHONES],
            ['audio-y-video/audio-y-video/parlantes-bocinas-cornetas-1',
             STEREO_SYSTEM],
            ['audio-y-video/audio-y-video/microfonos', MICROPHONE],
            # Impresion
            ['impresion/impresoras-y-escaneres', PRINTER],
            # Gaming
            ['gaming/equipos/notebooks', NOTEBOOK],
            ['gaming/equipos/monitores', MONITOR],
            ['gaming/componentes/procesadores', PROCESSOR],
            ['gaming/componentes/tarjetas-madre', MOTHERBOARD],
            ['gaming/componentes/tarjetas-de-video', VIDEO_CARD],
            ['gaming/componentes/almacenamiento', SOLID_STATE_DRIVE],
            ['gaming/componentes/memoria-ram', RAM],
            ['gaming/componentes/enfriamiento', CPU_COOLER],
            ['gaming/componentes/fuentes-de-poder', POWER_SUPPLY],
            ['gaming/componentes/gabinetes', COMPUTER_CASE],
            ['gaming/accesorios/audifonos', HEADPHONES],
            ['gaming/accesorios/teclados-y-mouse', MOUSE],
            ['gaming/accesorios/sillas', GAMING_CHAIR],
            ['gaming/accesorios/accesorios', KEYBOARD],
            ['gaming/videojuegos/consolas', VIDEO_GAME_CONSOLE],
            # Apple
            ['apple/computadores/macbook', NOTEBOOK],
            ['apple/computadores/imac', ALL_IN_ONE],
            ['apple/computadores/ipad', TABLET],
            ['apple/accesorios/apple-watch', WEARABLE],
            ['apple/accesorios/teclados-y-mouse', MOUSE],
            ['apple/accesorios/apple-tv', HEADPHONES],
            ['apple/accesorios/monitores-studio', MONITOR],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page > 15:
                    raise Exception('Page overflow')

                url = 'https://notebookstore.cl/{}.html?p={}'.format(
                    category_path, page)
                print(url)

                soup = BeautifulSoup(session.get(url).text, 'html5lib')
                products = soup.findAll('li', 'product')

                if not products:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                for product in products:
                    product_url = product.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)

        if response.status_code == 404 or response.status_code == 500:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('span', {'itemprop': 'name'}).text
        sku = soup.find('div', {'itemprop': 'sku'}).text

        stock = 0
        stock_container = soup.find('div', 'product-stock')

        if stock_container:
            stock = int(stock_container.text.strip().split(
                ' ')[1].replace('+', ''))

        offer_price = Decimal(soup.find('span', 'efectivo').find(
            'span', 'price').text.replace('$', '').replace('.', '')
        ).quantize(Decimal('1.'))
        normal_price = (offer_price * Decimal(1.034)
                        ).quantize(Decimal('1.'))

        image_scripts = soup.findAll('script', {'type': 'text/x-magento-init'})
        picture_urls = []

        for script in image_scripts:
            if 'mage/gallery/gallery' in script.text:
                image_data = json.loads(script.text)[
                    '[data-gallery-role=gallery-placeholder]'][
                    'mage/gallery/gallery']['data']
                for data in image_data:
                    picture_urls.append(data['img'])

        description = html_to_markdown(
            str(soup.find('div', 'description')))

        if len(sku) > 50:
            sku = sku[0:50]

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
