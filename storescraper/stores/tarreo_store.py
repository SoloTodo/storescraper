import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, MONITOR, \
    KEYBOARD_MOUSE_COMBO, MOUSE, KEYBOARD, STEREO_SYSTEM, \
    SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, RAM, MOTHERBOARD, \
    PROCESSOR, CPU_COOLER, VIDEO_GAME_CONSOLE, GAMING_CHAIR, HEADPHONES, \
    GAMING_DESK, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TarreoStore(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_CARD,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            MOUSE, KEYBOARD,
            STEREO_SYSTEM,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_GAME_CONSOLE,
            GAMING_CHAIR,
            HEADPHONES,
            GAMING_DESK,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audio-y-video/audifonos-y-accesorios/audifonos', HEADPHONES],
            ['accesorios-y-perifericos/combo-accesorios',
             KEYBOARD_MOUSE_COMBO],
            ['accesorios-y-perifericos/mouses-mousespads-y-accesorios', MOUSE],
            ['accesorios-y-perifericos/teclados', KEYBOARD],
            ['audio-y-video/speakers', STEREO_SYSTEM],
            ['componentes/almacenamiento', SOLID_STATE_DRIVE],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/gabinetes', COMPUTER_CASE],
            ['componentes/memorias', RAM],
            ['componentes/placas-madre', MOTHERBOARD],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/refrigeracion-y-ventiladores', CPU_COOLER],
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['juegos----consolas/consolas', VIDEO_GAME_CONSOLE],
            ['mobiliario-gamer/sillas-gamer', GAMING_CHAIR],
            ['mobiliario-gamer/sillones-gamer', GAMING_CHAIR],
            ['monitores', MONITOR],
            ['mobiliario-gamer/mesas-y-escritorios', GAMING_DESK],
            ['audio-y-video/microfonos', MICROPHONE]
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
                url_webpage = 'https://www.tarreo.store/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'section', 'vtex-product-summary-2-x-container')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.tarreo.store' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        match = re.search('__STATE__ = (.+)', response.text)
        product_data = json.loads(match.groups()[0])

        base_json_key = list(product_data.keys())[0]
        product_specs = product_data[base_json_key]

        name = product_specs['productName']
        key = product_specs['productId']
        sku = product_specs['productReference']
        description = html_to_markdown(product_specs.get('description', None))

        part_number_key = '{}.properties.0'.format(base_json_key)

        if product_data.get(part_number_key, {}).get('name', '') == \
                'Part Number':
            part_number = product_data[part_number_key]['values']['json'][0]
        else:
            part_number = None

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(pricing_data['Price'])
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
            price,
            price,
            'CLP',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
