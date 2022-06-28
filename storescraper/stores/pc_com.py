import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown
from storescraper.categories import PROCESSOR, RAM, VIDEO_CARD, \
    SOLID_STATE_DRIVE, EXTERNAL_STORAGE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, \
    HEADPHONES, MONITOR, MOUSE, KEYBOARD, STORAGE_DRIVE, CPU_COOLER, \
    MOTHERBOARD, GAMING_CHAIR, VIDEO_GAME_CONSOLE, MEMORY_CARD, \
    USB_FLASH_DRIVE, STEREO_SYSTEM, GAMING_DESK, MICROPHONE, CASE_FAN


class PcCom(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            RAM,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            HEADPHONES,
            MONITOR,
            MOUSE,
            KEYBOARD,
            STORAGE_DRIVE,
            CPU_COOLER,
            MOTHERBOARD,
            GAMING_CHAIR,
            VIDEO_GAME_CONSOLE,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            STEREO_SYSTEM,
            GAMING_DESK,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['consolas', VIDEO_GAME_CONSOLE],
            ['procesadores', PROCESSOR],
            ['placas-madres', MOTHERBOARD],
            ['memorias-ram', RAM],
            ['tarjetas-de-video', VIDEO_CARD],
            ['discos-duros', STORAGE_DRIVE],
            ['unidades-de-estado-solido', SOLID_STATE_DRIVE],
            ['disco-duro-pc', STORAGE_DRIVE],
            ['discos-duros/discos-duros-notebook', STORAGE_DRIVE],
            ['discos-duros/discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['enfriamiento/refrigeracion-liquida', CPU_COOLER],
            ['enfriamiento/cooler-pc', CPU_COOLER],
            ['enfriamiento/ventiladores-pc', CASE_FAN],
            ['almacenamiento/memoriasd', MEMORY_CARD],
            ['almacenamiento/microsd', MEMORY_CARD],
            ['almacenamiento/pendrive', USB_FLASH_DRIVE],
            ['audio/audifonos-gamer', HEADPHONES],
            ['audio/audifonos-bluetooth', HEADPHONES],
            ['audio/audifonos-in-ear', HEADPHONES],
            ['audio/parlantes-portatiles', STEREO_SYSTEM],
            ['audio/parlantes-pc', STEREO_SYSTEM],
            ['monitores-y-accesorios/monitores', MONITOR],
            ['perifericos/mouse-alambricos', MOUSE],
            ['perifericos/mouse-inalambricos', MOUSE],
            ['perifericos/teclado-alambricos', KEYBOARD],
            ['perifericos/teclado-inalambricos', KEYBOARD],
            ['zona-gamers/mouse-gamers', MOUSE],
            ['zona-gamers/teclados-membrana', KEYBOARD],
            ['zona-gamers/teclados-mecanicos', KEYBOARD],
            ['zona-gamers/sillas-gamers', GAMING_CHAIR],
            ['zona-gamer/escritorios-gamers', GAMING_DESK],
            ['audio/microfonos', MICROPHONE]
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page > 10:
                    raise Exception('Page overflow')

                url = 'https://pccom.cl/categoria-producto/{}/page/{}/' \
                    .format(category_path, page)
                response = session.get(url)

                soup = BeautifulSoup(response.text, 'html.parser')
                products = soup.findAll('li', 'product')

                if not products:
                    if page == 1:
                        logging.warning('Empty path: {}'.format(url))
                    break

                for product in products:
                    product_url = product.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('=')[1]

        stock_container = soup.find('p', 'stock')

        if not stock_container:
            input_qty = soup.find('input', 'qty')
            if not input_qty:
                return []
            else:
                stock = -1
        else:
            if 'disponible' in stock_container.text:
                stock = int(stock_container.text.split(' disp')[0])
            else:
                stock = 0

        price_container = soup.find('p', 'price')
        if price_container.find('ins'):
            price_container = price_container.find('ins')

        price = Decimal(remove_words(price_container.text))
        picture_containers = soup.findAll(
            'div', 'woocommerce-product-gallery__image')

        picture_urls = [ic.find('img')['src'] for ic in picture_containers
                        if ic['data-thumb']]

        description = html_to_markdown(
            str(soup.find('div', 'woocommerce-Tabs-panel--description')))

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
