import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, POWER_SUPPLY, CPU_COOLER, \
    COMPUTER_CASE, RAM, MONITOR, MOTHERBOARD, PROCESSOR, VIDEO_CARD, WEARABLE, \
    STEREO_SYSTEM, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


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
            HEADPHONES
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
            ['wearables', WEARABLE],
            ['audio/speakers', STEREO_SYSTEM],
            ['audio/audifonos', HEADPHONES]
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
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('main', 'site-main') \
                    .find('ul', 'products')
                if soup.find('div', 'info-404'):
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
        import pdb
        pdb.set_trace()

        product_container = soup.find('div', 'single-product-wrapper')
        name = product_container.find('h1', 'product_title').text
        normal_price = Decimal(
            product_container.find('div', 'hprice').text.split('$')[
                1].replace(
                '.', ''))
        if product_container.find('ins'):
            offer_price = Decimal(
                remove_words(
                    product_container.find('ins').text))
        else:
            offer_price = Decimal(
                remove_words(
                    product_container.find('span', 'electro-price').text))
        if soup.find('form', 'variations_form cart'):
            products = []
            variations = json.loads(soup.find('form', 'variations_form cart')['data-product_variations'])
            for variation in variations:
                vartion_name = name + ' - ' + variation['attributes'][
                    'attribute_pa_color']
                sku = str(variation['variation_id'])
                if BeautifulSoup(variation['availability_html'],
                                 'html.parser').text.split()[0] == 'Agotado':
                    stock = 0
                else:
                    stock = int(
                        BeautifulSoup(variation['availability_html'],
                                      'html.parser').text.split()[0])
                picture_urls = [variation['image']['url']]
                p = Product(
                    vartion_name,
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
            sku = product_container.find('a', 'add-to'
                                              '-compare'
                                              '-link')[
                'data-product_id']
            stock_container = product_container.find('p', 'stock').text.split()
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
