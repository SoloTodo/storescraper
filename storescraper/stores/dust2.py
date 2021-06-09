import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_GAME_CONSOLE, MOUSE, KEYBOARD, \
    HEADPHONES, STEREO_SYSTEM, GAMING_CHAIR, COMPUTER_CASE, CPU_COOLER, RAM, \
    POWER_SUPPLY, PROCESSOR, MOTHERBOARD, VIDEO_CARD, STORAGE_DRIVE, \
    MEMORY_CARD, EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, MONITOR, \
    KEYBOARD_MOUSE_COMBO, NOTEBOOK, TABLET
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Dust2(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_GAME_CONSOLE,
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            STEREO_SYSTEM,
            GAMING_CHAIR,
            COMPUTER_CASE,
            CPU_COOLER,
            RAM,
            POWER_SUPPLY,
            PROCESSOR,
            MOTHERBOARD,
            VIDEO_CARD,
            STORAGE_DRIVE,
            MEMORY_CARD,
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            NOTEBOOK,
            TABLET
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['consolas', VIDEO_GAME_CONSOLE],
            ['mundo-gamer/mouse-gamer', MOUSE],
            ['computacion-y-electronica/perifericos/mouse-perifericos', MOUSE],
            ['mundo-gamer/teclados-gamer', KEYBOARD],
            ['computacion-y-electronica/perifericos/teclados-perifericos',
             KEYBOARD],
            ['mundo-gamer/audifonos-gamer', HEADPHONES],
            ['computacion-y-electronica/audio/audifonos-audio', HEADPHONES],
            ['mundo-gamer/parlantes-gamer', STEREO_SYSTEM],
            ['computacion-y-electronica/audio/parlantes-audio', STEREO_SYSTEM],
            ['mundo-gamer/sillas', GAMING_CHAIR],
            ['computacion-y-electronica/componentes-de-pc/gabinetes',
             COMPUTER_CASE],
            ['computacion-y-electronica/componentes-de-pc/cooler-para-cpu',
             CPU_COOLER],
            ['computacion-y-electronica/componentes-de-pc/memorias-ram', RAM],
            ['computacion-y-electronica/notebooks/memorias-ram-notebooks',
             RAM],
            ['computacion-y-electronica/componentes-de-pc/fuentes-de-poder',
             POWER_SUPPLY],
            ['computacion-y-electronica/componentes-de-pc/procesadores',
             PROCESSOR],
            ['computacion-y-electronica/componentes-de-pc/placas-madres',
             MOTHERBOARD],
            ['computacion-y-electronica/componentes-de-pc/tarjetas-de-video',
             VIDEO_CARD],
            ['computacion-y-electronica/almacenamiento/ssd-y-discos-duros',
             STORAGE_DRIVE],
            ['computacion-y-electronica/almacenamiento/tarjetas-de-memoria',
             MEMORY_CARD],
            ['computacion-y-electronica/almacenamiento/discos-y-ssd-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['computacion-y-electronica/almacenamiento/pendrive',
             USB_FLASH_DRIVE],
            ['computacion-y-electronica/monitores', MONITOR],
            ['computacion-y-electronica/perifericos/combo-teclado-y-mouse',
             KEYBOARD_MOUSE_COMBO],
            ['computacion-y-electronica/notebooks/equipos', NOTEBOOK],
            ['computacion-y-electronica/tablets-e-readers', TABLET]
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
                url_webpage = 'https://dust2.gg/categoria-producto/{}/page' \
                              '/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
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
        name = soup.find('h3', 'product_title').text

        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]
        variants = soup.find('form', 'variations_form cart')
        if variants:
            products = []
            json_variants = json.loads(variants['data-product_variations'])
            for variant in json_variants:
                variant_name = name + '-' + variant['sku']
                variant_sku = str(variant['variation_id'])
                variant_stock = 0 if variant['max_qty'] == '' else variant[
                    'max_qty']
                variant_normal_price = Decimal(variant['display_price'])
                variant_offer_price = Decimal(
                    round(variant['display_price'] * 0.97))
                p = Product(
                    variant_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    variant_sku,
                    variant_stock,
                    variant_normal_price,
                    variant_offer_price,
                    'CLP',
                    sku=variant_sku,
                    picture_urls=picture_urls,

                )
                products.append(p)

            return products
        else:
            sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                1]
            if soup.find('p', 'stock out-of-stock'):
                stock = 0
            else:
                stock = int(soup.find('span', 'woostify-single-product'
                                              '-stock-label').text.strip()
                            .split()[4])
            normal_price = Decimal(remove_words(soup.find('p', 'price').text))
            offer_price = Decimal(
                remove_words(soup.find('h3', {'id': 'precio2'}).text))

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
                picture_urls=picture_urls,

            )
            return [p]
