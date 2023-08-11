import base64
import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import STORAGE_DRIVE, TABLET, STEREO_SYSTEM, \
    KEYBOARD, HEADPHONES, MOUSE, WEARABLE, VIDEO_GAME_CONSOLE, MICROPHONE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, \
    session_with_proxy


class CasaRoyal(StoreWithUrlExtensions):
    url_extensions = [
        ['audio/audifonos', HEADPHONES],
        ['audio/portable', STEREO_SYSTEM],
        ['audio/parlantes', STEREO_SYSTEM],
        ['audio/hogar', STEREO_SYSTEM],
        ['audifono', HEADPHONES],
        ['computacion/almacenamiento', STORAGE_DRIVE],
        ['computacion/tablet-y-proyectores/tablets', TABLET],
        ['computacion/accesorios-computacion/teclados-de-computacion',
         KEYBOARD],
        ['computacion/accesorios-computacion/mouse', MOUSE],
        ['computacion/accesorios-computacion/parlantes-de-computacion',
         STEREO_SYSTEM],
        ['computacion/accesorios-computacion/teclados', KEYBOARD],
        ['computacion/accesorios-computacion/parlantes-computacion',
         STEREO_SYSTEM],
        ['telefonia/wearables', WEARABLE],
        ['telefonia/audifonos', HEADPHONES],
        ['gamer/consolas', VIDEO_GAME_CONSOLE],
        ['gamer/audifonos-gamer', HEADPHONES],
        ['gamer/teclados-gamer', KEYBOARD],
        ['gamer/mouse-gamer', MOUSE],
        ['gamer/mouse', MOUSE],
        ['gamer/teclados', KEYBOARD],
        ['electronica-y-electricidad/computacion/mouse', MOUSE],
        ['electronica-y-electricidad/computacion/teclados-de-'
         'computacion.html', KEYBOARD],
        ['audio/microfonos', MICROPHONE]
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)

        done = False
        page = 0
        print(url_extension)

        while not done:
            if page >= 15:
                raise Exception('Page overflow: ' + url_extension)

            facets = [{'key': 'c', 'value': x}
                      for x in url_extension.split('/')]

            variables = {
                'from': page * 20,
                'to': (page + 1) * 20 - 1,
                'selectedFacets': facets
            }

            # The sha256Hash may change

            payload = {
                'persistedQuery': {
                    'version': 1,
                    'sha256Hash': '40e207fe75d9dce4dfb3154442da4615'
                                  'f2b097b53887a0ae5449eb92d42e84db',
                    'sender': 'vtex.store-resources@0.x',
                    'provider': 'vtex.search-graphql@0.x'
                },
                'variables': base64.b64encode(json.dumps(
                    variables).encode('utf-8')).decode('utf-8')
            }

            endpoint = 'https://www.casaroyal.cl/_v/segment/graphql/v1?' \
                       'extensions={}'.format(json.dumps(payload))
            response = session.get(endpoint)

            products_data = response.json()['data']['productSearch'][
                'products']

            if not products_data:
                break

            for idx, product_data in enumerate(products_data):
                product_url = 'https://www.casaroyal.cl/{}/p'.format(
                    product_data['linkText'])
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        product_data = json.loads(str(soup.find(
            'template', {'data-varname': '__STATE__'}).find(
            'script').contents[0]))

        base_json_keys = list(product_data.keys())

        if not base_json_keys:
            return []

        base_json_key = base_json_keys[0]
        product_specs = product_data[base_json_key]

        key = product_specs['productId']
        name = product_specs['productName']
        sku = product_specs['productReference']
        description = html_to_markdown(product_specs.get('description', None))

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        price = Decimal(pricing_data['Price'])

        if not price:
            return []

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
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
