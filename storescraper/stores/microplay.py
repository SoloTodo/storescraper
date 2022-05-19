import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import COMPUTER_CASE, GAMING_CHAIR, HEADPHONES, \
    KEYBOARD, MEMORY_CARD, MICROPHONE, MONITOR, MOUSE, POWER_SUPPLY, \
    STORAGE_DRIVE, USB_FLASH_DRIVE, VIDEO_CAMERA, VIDEO_GAME_CONSOLE, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Microplay(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            GAMING_CHAIR,
            HEADPHONES,
            KEYBOARD,
            MEMORY_CARD,
            MICROPHONE,
            MONITOR, STORAGE_DRIVE,
            MOUSE,
            POWER_SUPPLY,
            USB_FLASH_DRIVE,
            VIDEO_GAME_CONSOLE,
            VIDEO_CAMERA,
            WEARABLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['juegos', {'consolas': 'consola'}, VIDEO_GAME_CONSOLE],
            ['juegos', {'accesorios': 'audifonos-16'}, HEADPHONES],  # Play 5
            ['juegos', {'accesorios': 'audifonos-11'}, HEADPHONES],  # Play 4
            ['juegos', {'accesorios': 'audifonos-13'}, HEADPHONES],  # Switch
            ['juegos', {'accesorios': 'audifonos-5'}, HEADPHONES],  # Xbox
            ['juegos', {'accesorios': 'audifonos-3'}, HEADPHONES],  # Play 3
            ['juegos', {'accesorios': 'audifonos-7'}, HEADPHONES],  # PC
            ['juegos', {'plataformas': 'pc',
                        'accesorios': 'microfonos-13'}, MICROPHONE],
            ['juegos', {'plataformas': 'pc', 'accesorios': 'mouse-3'}, MOUSE],
            ['juegos', {'plataformas': 'pc',
                        'accesorios': 'sillas-gamer'}, GAMING_CHAIR],
            ['juegos', {'plataformas': 'pc',
                        'accesorios': 'teclados-5'}, KEYBOARD],
            ['gamer', {'categorias': 'audifonos-2'}, HEADPHONES],
            ['gamer', {'categorias': 'fuentes-de-poder-2'}, POWER_SUPPLY],
            ['gamer', {'categorias': 'monitores'}, MONITOR],
            ['gamer', {'categorias': 'gabinetes'}, COMPUTER_CASE],
            ['gamer', {'categorias': 'teclados-4'}, KEYBOARD],
            ['gamer', {'categorias': 'mouse-2'}, MOUSE],
            ['gamer', {'categorias': 'sillas-gamer-2'}, GAMING_CHAIR],
            ['computacion', {'categorias': 'discos-duros'}, STORAGE_DRIVE],
            ['computacion', {
                'categorias': 'memorias-sdmicro-sd-2'}, MEMORY_CARD],
            ['computacion', {'categorias': 'audifonos-14'}, HEADPHONES],
            ['computacion', {'categorias': 'microfonos-15'}, MICROPHONE],
            ['computacion', {'categorias': 'fuentes-de-poder'}, POWER_SUPPLY],
            ['computacion', {'categorias': 'monitores-2'}, MONITOR],
            ['computacion', {'categorias': 'gabinetes-2'}, COMPUTER_CASE],
            ['computacion', {'categorias': 'teclados-3'}, KEYBOARD],
            ['computacion', {'categorias': 'pendrive'}, USB_FLASH_DRIVE],
            ['computacion', {'categorias': 'mouse'}, MOUSE],
            ['computacion', {'categorias': 'mouse'}, MOUSE],
            ['audiovideo', {'categorias': 'audifonos-15'}, HEADPHONES],
            ['audiovideo', {'categorias': 'smartwatch'}, WEARABLE],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        for catalogo_name, filters, local_category in category_paths:
            if local_category != category:
                continue
            p = 1

            while True:
                if p > 20:
                    print(catalogo_name, filters)
                    raise Exception('Page overflow')

                request_pars = {
                    'familia': {'catalogo': catalogo_name},
                    'filtro': filters,
                    'control': []
                }
                request_pars = json.dumps(request_pars)

                params = {
                    'pars': request_pars,
                    'page': p
                }
                data = urllib.parse.urlencode(params)
                response = session.post('https://www.microplay.cl/productos/'
                                        'reader', data)

                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'card__item')

                if not product_containers:
                    break

                for container in product_containers:
                    product_url = 'https://www.microplay.cl' + \
                                  container.find('a')['href']
                    product_urls.append(product_url)

                p += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        if 'Producto no disponible' in page_source or 'h1' not in page_source:
            return []

        name = soup.find('h1').text.strip()
        sku = re.search(r'ecomm_prodid: (\d+)', page_source).groups()[0]

        price_container = soup.find('span', 'text_web')

        if price_container:
            price = remove_words(
                price_container.find('strong').find('p').nextSibling)
        else:
            price_container = soup.find('span', 'oferta')
            if not price_container:
                return []
            price = remove_words(price_container.find('b').text)

        price = Decimal(price)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'box-descripcion'})))
        picture_urls = [tag['href'] for tag in
                        soup.find('div', 'owl-carousel').findAll(
                            'a', 'fancybox')]

        if soup.find('span', 'fecha-lanzamiento'):
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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
