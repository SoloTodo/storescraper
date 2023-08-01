from collections import defaultdict
from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import MONITOR, PROCESSOR, STEREO_SYSTEM, \
    VIDEO_CARD, NOTEBOOK, GAMING_CHAIR, VIDEO_GAME_CONSOLE, WEARABLE, CELL
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class TodoGeek(StoreWithUrlExtensions):
    OPEN_BOX_COLLECTION = 401041227988
    REFURBISHED_COLLECTION = 401041326292
    ESPERALO_Y_PAGA_MENOS_COLLECTION = 411533082836

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

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('Page overflow: ' + url_extension)
            url_webpage = 'https://todogeek.cl/collections/{}?' \
                          'page={}'.format(url_extension, page)
            res = session.get(url_webpage)
            soup = BeautifulSoup(res.text, 'html.parser')
            product_containers = soup.findAll('product-card')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find(
                    'h3', 'product-card_title').find('a')['href']
                product_urls.append('https://todogeek.cl' + product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        shipping_rules = cls._get_shipping_rules(response)

        json_match = re.search(r'var otEstProduct = (.+)\n', response.text)
        json_data = json.loads(json_match.groups()[0])

        collections_endpoint = 'https://apps3.omegatheme.com/' \
                               'estimated-shipping/client/services/' \
                               '_shopify.php?shop=todogeek4.myshopify.com&' \
                               'action=getCollectionsByProductId' \
                               '&productId=' + str(json_data['id'])
        collections = session.get(collections_endpoint).json()

        rules = shipping_rules['product'][str(json_data['id'])]

        for collection in collections:
            rules.extend(shipping_rules['collection'][str(collection)])

        if not rules:
            print('No rules: ' + url)

        rules.sort(key=lambda rule: int(rule['shipping_method']['position']))
        preventa = rules and int(rules[0]['minimum_days']) > 1

        if not preventa and rules:
            for rule in rules[1:]:
                if int(rule['minimum_days']) > 1:
                    raise Exception('Conflicting rules found')

        category_tags = soup.find(
            'span', text='Categoria: ').parent.findAll('a')
        assert category_tags

        for tag in category_tags:
            if 'ESPERALO' in tag.text.upper() or \
                    'ESPERALO' in tag['href'].upper():
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
            offer_price = (Decimal(variant['price']) /
                           Decimal(100)).quantize(0)
            normal_price = (offer_price * Decimal('1.035')).quantize(0)

            if preventa or a_pedido or \
                    cls.ESPERALO_Y_PAGA_MENOS_COLLECTION in collections or \
                    'RESERVA' in description.upper() or \
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
                normal_price,
                offer_price,
                'CLP',
                picture_urls=picture_urls,
                description=description,
                condition=condition
            )
            products.append(p)
        return products

    @classmethod
    def _get_shipping_rules(cls, response):
        match = re.search(r'\sotEstAppData = (.+)', response.text)
        json_data = json.loads(match.groups()[0])
        # print(json.dumps(json_data))
        raw_rules = json_data['data']['app']

        shipping_methods_dict = {
            x['id']: x
            for x in raw_rules['shippingMethods']
        }

        shipping_rules_dict = {}

        for shipping_rule in raw_rules['estimatedDate']['specificRules']:
            shipping_rule['shipping_method'] = \
                shipping_methods_dict[shipping_rule['shipping_method_id']]
            shipping_rules_dict[shipping_rule['id']] = shipping_rule

        shipping_rules = {
            'product': defaultdict(lambda: []),
            'collection': defaultdict(lambda: [])
        }
        for specificTarget in raw_rules['estimatedDate'][
                'specificRuleTargets']:
            rule = shipping_rules_dict[specificTarget['rule_id']]

            if rule['enable'] != '1':
                raise Exception('Disabled rule?')

            shipping_rules[specificTarget['type']][
                specificTarget['value']].append(rule)

        # print(json.dumps(shipping_rules))
        return shipping_rules
