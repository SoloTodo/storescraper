import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, VIDEO_CARD, MONITOR, KEYBOARD_MOUSE_COMBO, \
    COMPUTER_CASE, EXTERNAL_STORAGE_DRIVE, POWER_SUPPLY, HEADPHONES, \
    CPU_COOLER, GAMING_CHAIR, NOTEBOOK, VIDEO_GAME_CONSOLE, KEYBOARD, MOUSE, \
    MEMORY_CARD, PRINTER, STEREO_SYSTEM, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class KillStore(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            PROCESSOR,
            RAM,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            COMPUTER_CASE,
            EXTERNAL_STORAGE_DRIVE,
            POWER_SUPPLY,
            HEADPHONES,
            CPU_COOLER,
            GAMING_CHAIR,
            NOTEBOOK,
            VIDEO_GAME_CONSOLE,
            KEYBOARD,
            MOUSE,
            MEMORY_CARD,
            STEREO_SYSTEM,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audio/audifonos', HEADPHONES],
            ['audio/monitores/activos', STEREO_SYSTEM],
            ['computacion/notebooks', NOTEBOOK],
            ['computacion/componentes/discos-internos', SOLID_STATE_DRIVE],
            ['computacion/componentes/fuentes', POWER_SUPPLY],
            ['computacion/componentes/gabinetes', COMPUTER_CASE],
            ['computacion/componentes/memoria-ram', RAM],
            ['computacion/componentes/placas-madre', MOTHERBOARD],
            ['computacion/componentes/procesadores', PROCESSOR],
            ['computacion/componentes/refrigeracion-y-ventiladores',
             CPU_COOLER],
            ['computacion/componentes/tarjetas-de-video', VIDEO_CARD],
            ['computacion/mouse-y-teclado/teclados', KEYBOARD],
            ['computacion/mouse-y-teclado/mouse', MOUSE],
            ['computacion/monitores', MONITOR],
            ['computacion/almacenamiento/discos-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['fotografia/almacenamiento/memorias-cf', MEMORY_CARD],
            ['fotografia/almacenamiento/memorias-cf-express', MEMORY_CARD],
            ['fotografia/almacenamiento/memorias-cfast', MEMORY_CARD],
            ['fotografia/almacenamiento/memorias-micro-sd', MEMORY_CARD],
            ['fotografia/almacenamiento/memorias-sd', MEMORY_CARD],
            ['fotografia/almacenamiento/memorias-xqd', MEMORY_CARD],
            ['video/almacenamiento/memorias', MEMORY_CARD],
            ['256?map=productClusterIds', MEMORY_CARD],
            ['257?map=productClusterIds', MEMORY_CARD],
            ['258?map=productClusterIds', PRINTER],
            ['computacion/sillas', GAMING_CHAIR],
            ['gaming', VIDEO_GAME_CONSOLE],
            ['audio/microfonos', MICROPHONE]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow: ' + url_extension)

                sep = '&' if '?' in url_extension else '?'
                url_webpage = 'https://www.killstore.cl/{}{}page={}'.format(
                    url_extension, sep, page)
                print(url_webpage)

                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                page_state_tag = soup.find(
                    'template', {'data-varname': '__STATE__'})
                page_state = json.loads(page_state_tag.text)
                done = True

                for key, value in page_state.items():
                    if key.startswith('Product:') and 'linkText' in value:
                        product_urls.append('https://www.killstore.cl/' +
                                            value['linkText'] + '/p')
                        done = False

                if done:
                    # if page == 0:
                    #     raise Exception(url_webpage)
                    break
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        product_data = json.loads(
            soup.find('template', {'data-varname': '__STATE__'}).text)

        base_json_keys = list(product_data.keys())

        if not base_json_keys:
            return []

        base_json_key = base_json_keys[0]
        product_specs = product_data[base_json_key]

        name = product_specs['productName']
        key = product_specs['productId']
        sku = product_specs['productReference']
        description = html_to_markdown(product_specs.get('description', None))

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        normal_price = Decimal(pricing_data['Price'])
        offer_price = (normal_price * Decimal('0.96')).quantize(0)
        stock = pricing_data['AvailableQuantity']

        picture_list_key = '{}.items.0'.format(base_json_key)
        picture_list_node = product_data[picture_list_key]
        picture_ids = [x['id'] for x in picture_list_node['images']]

        picture_urls = []
        for picture_id in picture_ids:
            picture_node = product_data[picture_id]
            picture_urls.append(picture_node['imageUrl'].split('?')[0])

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
            description=description,
        )

        return [p]
