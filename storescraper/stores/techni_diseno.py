import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, POWER_SUPPLY, MOUSE, KEYBOARD, MONITOR, RAM, \
    HEADPHONES, KEYBOARD_MOUSE_COMBO
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TechniDiseno(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            MOUSE,
            KEYBOARD,
            MONITOR,
            RAM,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebooks', NOTEBOOK],
            ['zona-gamer/accesorios-gamer', HEADPHONES],
            ['piezas-y-accesorios/teclados-mecanicos', KEYBOARD],
            ['piezas-y-accesorios/mouse-y-accesorios', MOUSE],
            ['kits-de-teclado/mouse', KEYBOARD_MOUSE_COMBO],
            ['monitores', MONITOR],
            ['memorias-ram/memorias-pc', RAM],
            ['memorias-ram/memorias-notebook', RAM],
            ['discos-duros/discos-solidos-ssd', SOLID_STATE_DRIVE],
            ['discos-duros/usados/discos-duros-para-notebooks', STORAGE_DRIVE],
            ['discos-duros/usados/discos-duros-para-macbook', STORAGE_DRIVE],
            ['discos-duros/para-consolas', STORAGE_DRIVE],
            ['piezas-y-accesorios/fuentes-de-poder', POWER_SUPPLY],
            ['zona-gamer', HEADPHONES],
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
                url_webpage = 'https://technidiseno.cl/{}?page={}'. \
                    format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('a', 'product-image')

                if not product_containers:
                    break

                for container in product_containers:
                    product_url = 'https://technidiseno.cl' + container['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        base_name = json_data['name']

        blacklist = ['REACONDICIONADO', 'USADO']

        for keyword in blacklist:
            if keyword in base_name.upper():
                condition = 'https://schema.org/RefurbishedCondition'
                break
        else:
            condition = 'https://schema.org/NewCondition'

        variants_match = re.search('var productInfo = (.+?);', response.text)
        if variants_match:
            variants_data = json.loads(variants_match.groups()[0])
            products = []
            for variant in variants_data:
                name = '{} ({})'.format(
                    base_name, variant['values'][0]['value']['name'])
                key = str(variant['variant']['id'])
                sku = variant['variant']['sku']
                price = Decimal(variant['variant']['price'])
                stock = variant['variant']['stock']
                picture_urls = [variant['image'].split('?')[0]]

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
                    condition=condition
                )
                products.append(p)

            return products
        else:
            if 'sku' in json_data:
                sku = json_data['sku']
            else:
                sku = ''

            stock_tag = soup.find('span', 'product-form-stock')
            if stock_tag:
                stock = int(stock_tag.text)
            else:
                stock = 0

            key = soup.find('form', 'product-form')['action'].split('/')[-1]

            price = Decimal(json_data['offers']['price'])
            picture_urls = [tag['src'] for tag in
                            soup.find('div', 'product-images').findAll('img')]

            p = Product(
                base_name,
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
                condition=condition
            )

            return [p]
