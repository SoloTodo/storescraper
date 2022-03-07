import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, COMPUTER_CASE, POWER_SUPPLY, \
    RAM, MONITOR, MOUSE, VIDEO_CARD, PROCESSOR, MOTHERBOARD, \
    KEYBOARD, CPU_COOLER, SOLID_STATE_DRIVE, GAMING_CHAIR, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class HardGaming(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            COMPUTER_CASE,
            POWER_SUPPLY,
            RAM,
            SOLID_STATE_DRIVE,
            MONITOR,
            MOUSE,
            VIDEO_CARD,
            PROCESSOR,
            MOTHERBOARD,
            KEYBOARD,
            CPU_COOLER,
            GAMING_CHAIR,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['gabinete', COMPUTER_CASE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['memorias', RAM],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['procesadores', PROCESSOR],
            ['placas-madres', MOTHERBOARD],
            ['teclados', KEYBOARD],
            ['refrigeracion', CPU_COOLER],
            ['sillas-gamer', GAMING_CHAIR],
            ['microfonos', MICROPHONE]
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
                url_webpage = 'https://www.hardgaming.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                base_url_store = 'https://www.hardgaming.cl'
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(base_url_store + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        base_name = soup.find('h1', 'product-form_title page-title').text
        picture_containers = soup.find('div', 'owl-thumbs product-page-thumbs '
                                              'overflow-hidden '
                                              'mt-3')
        if not picture_containers:
            picture_urls = [soup.find('div', 'product-images owl-carousel '
                                             'product-slider').find('img')[
                                'src'].split('?')[0]]
        else:
            picture_urls = [tag['src'].split('?')[0] for tag in
                            picture_containers.findAll('img')]

        variants_match = re.search(
            r'Jumpseller.productVariantListener'
            r'\(".qty-select select", {product: \'(.+)\'', response.text)
        variants = json.loads(variants_match.groups()[0])

        if variants:
            products = []
            for variant in variants:
                values = ' / '.join(x['value']['name']
                                    for x in variant['values'])
                name = '{} ({})'.format(base_name, values)
                sku = str(variant['variant']['id'])

                if 'PREVENTA' in base_name.upper():
                    stock = 0
                elif variant['variant']['stock']:
                    stock = -1
                else:
                    stock = 0

                price = Decimal(variant['variant']['price']).quantize(0)

                products.append(Product(
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
                    picture_urls=picture_urls
                ))
            return products
        else:
            sku_container = soup.find('form', 'product-form')['action']
            sku = re.search(r"/(\d+)$", sku_container).groups()[0]
            stock_container = soup \
                .find('form', 'product-form form-horizontal') \
                .find('div',
                      'form-group product-stock product-out-stock text-center '
                      'hidden')

            if 'PREVENTA' in base_name.upper():
                stock = 0
            elif not stock_container:
                stock = 0
            else:
                stock = -1

            price = Decimal(
                remove_words(soup.find('span', 'product-form_price').text))

            return [Product(
                base_name,
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
                picture_urls=picture_urls
            )]
