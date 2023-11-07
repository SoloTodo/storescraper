from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import MONITOR, PROCESSOR, STEREO_SYSTEM, \
    VIDEO_CARD, NOTEBOOK, GAMING_CHAIR, VIDEO_GAME_CONSOLE, WEARABLE, CELL, \
    KEYBOARD
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class TodoGeek(StoreWithUrlExtensions):
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
        ['Teclados', KEYBOARD],
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

        match = re.search(r'"delivery__app_setting": (.+),', response.text)
        json_data = json.loads(match.groups()[0])
        order_ready_day_range = \
        json_data['main_delivery_setting']['order_delivery_day_range']
        max_day = max(order_ready_day_range)

        match = re.search(r'const productJson = (.+);', response.text)
        json_data = json.loads(match.groups()[0])

        category_tags = soup.find(
            'span', text='Categoria: ').parent.findAll('a')
        assert category_tags

        if max_day > 2:
            a_pedido = True
        else:
            for tag in category_tags:
                if 'ESPERALO' in tag.text.upper() or \
                        'ESPERALO' in tag['href'].upper():
                    a_pedido = True
                    break
                if 'RESERVA' in tag.text.upper() or \
                        'RESERVA' in tag['href'].upper():
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

            if a_pedido or \
                    'RESERVA' in description.upper() or \
                    'VENTA' in name.upper():
                stock = 0
            elif variant['available']:
                stock = -1
            else:
                stock = 0

            for tag in category_tags:
                if 'OPEN BOX' in tag.text.upper() or \
                        'OPEN BOX' in tag['href'].upper():
                    condition = 'https://schema.org/OpenBoxCondition'
                    break
                if 'REACONDICIONADO' in tag.text.upper() or \
                        'REACONDICIONADO' in tag['href'].upper():
                    condition = 'https://schema.org/OpenBoxCondition'
                    break
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
