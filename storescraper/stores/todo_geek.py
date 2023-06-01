from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import MONITOR, PROCESSOR, STEREO_SYSTEM, \
    VIDEO_CARD, NOTEBOOK, GAMING_CHAIR, VIDEO_GAME_CONSOLE, WEARABLE, CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TodoGeek(Store):
    OPEN_BOX_COLLECTION = 401041227988
    REFURBISHED_COLLECTION = 401041326292

    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            VIDEO_CARD,
            MONITOR,
            STEREO_SYSTEM,
            NOTEBOOK,
            GAMING_CHAIR,
            WEARABLE,
            VIDEO_GAME_CONSOLE,
            CELL,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['procesadores', PROCESSOR],
            ['tarjetas-graficas', VIDEO_CARD],
            ['monitores', MONITOR],
            ['parlantes-inteligentes', STEREO_SYSTEM],
            ['laptops-computer', NOTEBOOK],
            ['sillas-gamer', GAMING_CHAIR],
            ['watches', WEARABLE],
            ['consolas', VIDEO_GAME_CONSOLE],
            ['celulares', CELL],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://todogeek.cl/collections/{}?' \
                              'page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-grid-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find(
                        'h5', 'product-name').find('a')['href']
                    product_urls.append('https://todogeek.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        blacklist = cls._get_blackslist(response)

        # Manually add the "Espéralo y paga menos" collection to the blacklist
        # because the website "a pedido" rules sometimes do not show the
        # warning
        blacklist['collection'].append('411533082836')

        match = re.search('product: (.+), onVariantSelected', response.text)
        json_data = json.loads(match.groups()[0])

        collections_endpoint = 'https://apps3.omegatheme.com/' \
                               'estimated-shipping/client/services/' \
                               '_shopify.php?shop=todogeek4.myshopify.com&' \
                               'action=getCollectionsByProductId' \
                               '&productId=' + str(json_data['id'])
        collections = session.get(collections_endpoint).json()
        preventa = False

        if str(json_data['id']) in blacklist['product']:
            print('Product blacklist: ' + str(json_data['id']))
            preventa = True

        for collection in collections:
            if str(collection) in blacklist['collection']:
                print('Collection blacklist: ' + str(collection))
                preventa = True

        category_tags = soup.find('li', 'category').findAll('a')
        assert category_tags

        for tag in category_tags:
            if 'ESPERALO' in tag.text.upper() or 'ESPERALO' in tag['href'].upper():
                a_pedido = True
                break
        else:
            a_pedido = False

        picture_urls = []

        for picture in json_data['images']:
            picture_urls.append('https:' + picture)

        description = html_to_markdown(json_data['description'])

        products = []
        for variant in json_data['variants']:
            key = str(variant['id'])
            name = variant['name']
            price = (Decimal(variant['price']) /
                     Decimal(100)).quantize(0)

            if a_pedido or preventa or 'RESERVA' in description.upper() or \
                    'VENTA' in name.upper():
                stock = 0
            elif variant['available']:
                stock = -1
            else:
                stock = 0

            if cls.OPEN_BOX_COLLECTION in collections:
                condition = 'https://schema.org/OpenBoxCondition'
            elif cls.REFURBISHED_COLLECTION in collections:
                condition = 'https://schema.org/RefurbishedCondition'
            else:
                condition = 'https://schema.org/NewCondition'

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
                picture_urls=picture_urls,
                description=description,
                condition=condition
            )
            products.append(p)
        return products

    @classmethod
    def _get_blackslist(cls, response):
        match = re.search(r'\sotEstAppData = (.+)', response.text)
        json_data = json.loads(match.groups()[0])
        # print(json.dumps(json_data))
        raw_rules = json_data['data']['app']

        shipping_methods_dict = {
            x['id']: x
            for x in raw_rules['shippingMethods']
        }

        blacklist = {
            'product': [],
            'collection': []
        }
        for rule in raw_rules['estimatedDate']['specificRuleTargets']:
            if int(shipping_methods_dict[rule[
                    'shipping_method_id']]['minimum_days']) > 1:
                # print(json.dumps(rule))
                # print(json.dumps(
                # shipping_methods_dict[rule['shipping_method_id']]))
                blacklist[rule['type']].append(rule['value'])
        # print(json.dumps(blacklist))
        return blacklist
