import json
import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, KEYBOARD, MOUSE, MONITOR, \
    WEARABLE, POWER_SUPPLY, CPU_COOLER, COMPUTER_CASE, RAM, GAMING_CHAIR, \
    STEREO_SYSTEM, MOTHERBOARD, KEYBOARD_MOUSE_COMBO, GAMING_DESK, \
    MICROPHONE, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MiMallVirtual(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            KEYBOARD,
            MOUSE,
            MONITOR,
            WEARABLE,
            POWER_SUPPLY,
            CPU_COOLER,
            COMPUTER_CASE,
            RAM,
            GAMING_CHAIR,
            STEREO_SYSTEM,
            MOTHERBOARD,
            KEYBOARD_MOUSE_COMBO,
            GAMING_DESK,
            MICROPHONE,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['31-audifonos-gamer', HEADPHONES],
            ['36-gabinetes', COMPUTER_CASE],
            ['38-memorias', RAM],
            ['29-mouses', MOUSE],
            ['35-sillas', GAMING_CHAIR],
            ['30-teclados', KEYBOARD],
            ['41-fuentes-de-poder-psu', POWER_SUPPLY],
            ['47-parlantes', STEREO_SYSTEM],
            ['43-enfriador-liquido-cpu', CPU_COOLER],
            ['51-monitores-gamers', MONITOR],
            ['52-placas-madre', MOTHERBOARD],
            ['20-audifonos', HEADPHONES],
            ['19-teclados', KEYBOARD],
            ['24-mouse', MOUSE],
            ['27-monitores', MONITOR],
            ['32-relojes', WEARABLE],
            ['40-fuentes-de-poder-psu', POWER_SUPPLY],
            ['44-enfriador-liquido-cpu', CPU_COOLER],
            ['50-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['49-sillas', GAMING_CHAIR],
            ['21-escritorios', GAMING_DESK],
            ['39-microfonos', MICROPHONE],
            ['46-ventiladores', CASE_FAN],
            ['45-ventiladores', CASE_FAN],
        ]
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.mimallvirtual.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('article',
                                                  'product-miniature')
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
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        sku = soup.find('input', {'name': 'id_product'})['value']

        ajax_session = session_with_proxy(extra_args)
        ajax_session.headers['Content-Type'] = \
            'application/x-www-form-urlencoded; charset=UTF-8'
        base_product_data = ajax_session.post(
            'https://www.mimallvirtual.cl/index.php?controller=product'
            '&id_product=' + sku, 'ajax=1&action=refresh').json()
        variants_soup = BeautifulSoup(base_product_data['product_variants'],
                                      'html.parser')
        variant_tags = variants_soup.findAll('label')
        products = []

        if variant_tags:
            for variant_tag in variant_tags:
                attribute_name = variant_tag.find('span').text.strip()
                attribute_field = variant_tag.find('input')['name']
                attribute_value = variant_tag.find('input')['value']
                variant_endpoint = \
                    'https://www.mimallvirtual.cl/index.php?controller=' \
                    'product&id_product={}&{}={}'.format(
                        sku, urllib.parse.quote(attribute_field),
                        attribute_value)
                variant_data = ajax_session.post(
                    variant_endpoint, 'ajax=1&action=refresh').json()
                p = cls.get_product_from_json(variant_data, category)
                p.key += '_{}'.format(attribute_value)
                p.name += ' ({})'.format(attribute_name)
                products.append(p)
        else:
            products.append(cls.get_product_from_json(
                base_product_data, category))

        return products

    @classmethod
    def get_product_from_json(cls, product_json, category):
        name = product_json['product_title']
        url = product_json['product_url']
        product_soup = BeautifulSoup(product_json['product_details'],
                                     'html.parser')
        product_data = json.loads(
            product_soup.find('div').attrs['data-product'])
        sku = str(product_data['id_product'])
        part_number = product_data['reference']
        price = Decimal(product_data['price_amount'])
        stock = product_data['quantity']
        picture_urls = [tag['large']['url'] for tag in product_data['images']]

        return Product(
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
            part_number=part_number,
            picture_urls=picture_urls
        )
