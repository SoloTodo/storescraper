import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, POWER_SUPPLY, CPU_COOLER, \
    COMPUTER_CASE, RAM, MONITOR, MOTHERBOARD, PROCESSOR, VIDEO_CARD, \
    WEARABLE, STEREO_SYSTEM, HEADPHONES, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class SmartMobile(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            POWER_SUPPLY,
            CPU_COOLER,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            WEARABLE,
            STEREO_SYSTEM,
            HEADPHONES,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['smartphones', CELL],
            ['componentes-pc/fuente-de-poder', POWER_SUPPLY],
            ['componentes-pc/cooler', CPU_COOLER],
            ['componentes-pc/gabinete', COMPUTER_CASE],
            ['componentes-pc/memoria-ram', RAM],
            ['componentes-pc/monitor', MONITOR],
            ['componentes-pc/placa-madre', MOTHERBOARD],
            ['componentes-pc/procesador', PROCESSOR],
            ['componentes-pc/tarjeta-grafica', VIDEO_CARD],
            ['componentes-pc/accesorios-componentes-pc', CASE_FAN],
            ['wearables', WEARABLE],
            ['audio/speakers', STEREO_SYSTEM],
            ['audio/audifonos', HEADPHONES],
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
                url_webpage = 'https://smartmobile.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.find('main', 'site-main') \
                    .find('ul', 'products')

                if soup.find('div', 'info-404') or not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers.findAll('li', 'product'):
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

        product_container = soup.find('div', 'single-product-wrapper')
        name = product_container.find('h1', 'product_title').text

        if 'ENTREGA' in name.upper() and 'INMEDIATA' not in name.upper():
            force_unavailable = True
        else:
            force_unavailable = False

        if soup.find('form', 'variations_form cart'):
            products = []
            variations = json.loads(soup.find('form', 'variations_form cart')[
                                        'data-product_variations'])
            for variation in variations:
                variation_attribute = list(variation['attributes'].values())
                variation_name = name + ' (' + ' - '.join(
                    variation_attribute) + ')'
                sku = str(variation['variation_id'])
                offer_price = Decimal(variation['display_price'])
                normal_price = Decimal(
                    round(variation['display_price'] * 1.04))

                if force_unavailable:
                    stock = 0
                elif variation['availability_html'] == '':
                    stock = -1
                elif BeautifulSoup(variation['availability_html'],
                                   'html.parser').text.split()[0] == 'Agotado':
                    stock = 0
                else:
                    stock = int(
                        BeautifulSoup(variation['availability_html'],
                                      'html.parser').text.split()[0])
                picture_urls = [variation['image']['url']]
                p = Product(
                    variation_name,
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
                    picture_urls=picture_urls
                )
                products.append(p)
            return products
        else:
            price_info = int(json.loads(
                soup.find('script', {'type': 'application/ld+json'}).text)[
                                 '@graph'][1]['offers'][0][
                                 'priceSpecification']['price'])
            normal_price = Decimal(round(price_info * 1.04))
            offer_price = Decimal(price_info)
            sku = product_container.find('a', 'add-to-compare-link')[
                'data-product_id']

            if force_unavailable:
                stock = 0
            elif not product_container.find('p', 'stock'):
                stock = -1
            else:
                stock_container = product_container.find(
                    'p', 'stock').text.split()
                if stock_container[0] == 'Agotado':
                    stock = 0
                else:
                    stock = int(stock_container[0])

            picture_urls = [tag['src'] for tag in
                            soup.find('div',
                                      'woocommerce-product-gallery').findAll(
                                'img')]
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
                picture_urls=picture_urls

            )
            return [p]
