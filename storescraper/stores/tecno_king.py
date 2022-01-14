import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MOUSE, POWER_SUPPLY, \
    COMPUTER_CASE, MOTHERBOARD, VIDEO_CARD, PROCESSOR, CPU_COOLER, RAM, \
    SOLID_STATE_DRIVE, STORAGE_DRIVE, HEADPHONES, STEREO_SYSTEM, MONITOR, \
    GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class TecnoKing(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MOUSE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOTHERBOARD,
            VIDEO_CARD,
            PROCESSOR,
            CPU_COOLER,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            HEADPHONES,
            STEREO_SYSTEM,
            MONITOR,
            GAMING_CHAIR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebook-accesorios/notebooks-tradicionales', NOTEBOOK],
            ['notebook-accesorios/notebooks-ultralivianos', NOTEBOOK],
            ['perifericos/mouse', MOUSE],
            ['componentes-para-pc-notebook/fuente-de-poder', POWER_SUPPLY],
            ['componentes-para-pc-notebook/gabinetes', COMPUTER_CASE],
            ['componentes-para-pc-notebook/placas-madre', MOTHERBOARD],
            ['componentes-para-pc-notebook/tarjeta-grafica', VIDEO_CARD],
            ['componentes-para-pc-notebook/procesadores', PROCESSOR],
            ['componentes-para-pc-notebook/refrigeracion', CPU_COOLER],
            ['componentes-para-pc-notebook/almacenamiento/memoria-ram', RAM],
            ['componentes-para-pc-notebook/almacenamiento/discos-notebook',
             STORAGE_DRIVE],
            ['componentes-para-pc-notebook/almacenamiento/discos-ssd',
             SOLID_STATE_DRIVE],
            ['auriculares/auriculares-gamer', HEADPHONES],
            ['auriculares/auriculares-inalambricos', HEADPHONES],
            ['product-category/parlantes', STEREO_SYSTEM],
            ['product-category/zona-gaming/monitores', MONITOR],
            ['product-category/zona-gaming/silla-gamer', GAMING_CHAIR],
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

                url_webpage = 'https://tecnoking.cl/product-category/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'ast-grid-common-col')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        if soup.find('form', 'variations_form'):
            variations = json.loads(soup.find('form', 'variations_form')[
                                        'data-product_variations'])
            products = []
            for product in variations:
                variation_name = name + ' - ' + product['attributes'][
                    'attribute_pa_color']
                key = str(product['variation_id'])
                sku = product['sku']
                if product['is_in_stock']:
                    stock = -1
                else:
                    stock = 0
                price = Decimal(product['display_price'])
                picture_urls = [product['image']['src']]
                p = Product(
                    variation_name,
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

                )
                products.append(p)
            return products

        else:
            key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                -1]
            sku_tag = soup.find('span', 'sku')

            if sku_tag:
                sku = sku_tag.text.strip()
            else:
                sku = None

            if soup.find('p', 'stock out-of-stock'):
                stock = 0
            else:
                stock = -1
            if soup.find('p', 'price').find('ins'):
                price = Decimal(
                    remove_words(soup.find('p', 'price').find('ins').text))
            else:
                price_text = soup.find('p', 'price').text.strip()
                if not price_text:
                    return []
                price = Decimal(remove_words(price_text))
            picture_urls = [tag['src'] for tag in soup.find('div',
                                                            'woocommerce-'
                                                            'product-'
                                                            'gallery').
                            findAll('img')]
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

            )
            return [p]
