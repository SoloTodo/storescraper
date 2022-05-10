import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, TABLET, HEADPHONES, \
    VIDEO_GAME_CONSOLE, GAMING_CHAIR, KEYBOARD, COMPUTER_CASE, RAM, \
    MOTHERBOARD, PROCESSOR, VIDEO_CARD, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, MEMORY_CARD, MONITOR, PRINTER, STEREO_SYSTEM, \
    MICROPHONE, CPU_COOLER, POWER_SUPPLY
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class ZonaPortatil(Store):
    @classmethod
    def categories(cls):
        return [
            ALL_IN_ONE,
            NOTEBOOK,
            TABLET,
            HEADPHONES,
            VIDEO_GAME_CONSOLE,
            GAMING_CHAIR,
            KEYBOARD,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MEMORY_CARD,
            MONITOR,
            PRINTER,
            STEREO_SYSTEM,
            MICROPHONE,
            CPU_COOLER,
            POWER_SUPPLY,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computadores/all-in-one-todo-en-uno', ALL_IN_ONE],
            ['computadores/notebook', NOTEBOOK],
            ['computadores/tablets', TABLET],
            ['accesorios/audifonos-accesorios', HEADPHONES],
            ['accesorios/parlantes', STEREO_SYSTEM],
            ['accesorios/consolas', VIDEO_GAME_CONSOLE],
            ['accesorios/sillas-gamer', GAMING_CHAIR],
            ['accesorios/teclados-mouse', KEYBOARD],
            ['partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/memorias-notebook', RAM],
            ['partes-y-piezas/memorias-pc', RAM],
            ['partes-y-piezas/placas-madres', MOTHERBOARD],
            ['partes-y-piezas/procesadores/', PROCESSOR],
            ['partes-y-piezas/tarjetas-graficas', VIDEO_CARD],
            ['almacenamiento/discos-duros-pc', STORAGE_DRIVE],
            ['almacenamiento/discos-duros-notebook/', STORAGE_DRIVE],
            ['almacenamiento/discos-ssd', SOLID_STATE_DRIVE],
            ['almacenamiento/discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento/discos-duros-video-vigilancia', STORAGE_DRIVE],
            ['almacenamiento/memorias-flash', MEMORY_CARD],
            ['monitores-proyectores/monitores', MONITOR],
            ['impresoras', PRINTER],
            ['zona-gamer/fuente-de-poder', POWER_SUPPLY],
            ['zona-gamer/monitores-zona-gamer', MONITOR],
            ['zona-gamer/sillas-gamer', GAMING_CHAIR],
            ['zona-gamer/gabinetes-zona-gamer', COMPUTER_CASE],
            ['zona-gamer/audifonos', HEADPHONES],
            ['zona-gamer/teclados-mouse-zona-gamer', KEYBOARD],
            ['zona-gamer/microfonos', MICROPHONE],
            ['zona-gamer/refrigeracion', CPU_COOLER],
            ['zona-gamer/placas-madres-zona-gamer', MOTHERBOARD],
            ['zona-gamer/procesadores-zona-gamer', PROCESSOR],
            ['zona-gamer/tarjetas-graficas-zona-gamer', VIDEO_CARD],
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

                url_webpage = 'https://www.zonaportatil.cl/categoria-prod' \
                              'ucto/{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category')
                    break
                for container in product_containers:
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
        name = soup.find('h1', 'product_title').text
        if 'OPEN BOX' in name:
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'
        sku = soup.find('span', 'sku').text
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        if soup.find('p', 'price').find('ins'):
            normal_price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price_text = soup.find('p', 'price').text.strip()
            if not price_text:
                return []
            normal_price = Decimal(remove_words(price_text))
        offer_price = (normal_price * Decimal('0.95')).quantize(0)
        picture_urls = [tag['src'] for tag in soup.find('div', 'woocommerce'
                                                               '-product'
                                                               '-gallery')
                        .findAll('img')]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            condition=condition

        )
        return [p]
