import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, \
    HEADPHONES, GAMING_DESK, POWER_SUPPLY, COMPUTER_CASE, RAM, MONITOR, \
    MOUSE, MOTHERBOARD, PROCESSOR, CPU_COOLER, GAMING_CHAIR, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class FibraNet(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            HEADPHONES,
            GAMING_DESK,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOUSE,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            GAMING_CHAIR,
            VIDEO_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento-externo', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento-interno', STORAGE_DRIVE],
            ['audifonos', HEADPHONES],
            ['escritorios', GAMING_DESK],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['memorias-ram', RAM],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['placas-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['refrigeracion', CPU_COOLER],
            ['sillas', GAMING_CHAIR],
            ['sillas-gamer', GAMING_CHAIR],
            ['tarjetas-de-video', VIDEO_CARD]
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
                url_webpage = 'https://www.fibranet.cl/index.php/categoria' \
                              '-producto/{}/?product-page={}'.format(
                                url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

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
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[1]
        json_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)

        for json_entry in json_data['@graph']:
            if json_entry['@type'] == 'Product':
                product_data = json_entry
                break
        else:
            raise Exception('No product data found')

        name = product_data['name']
        sku = product_data['sku']
        offer_price = Decimal(product_data['offers'][0]['price'])
        normal_price = (offer_price * Decimal('1.035')).quantize(0)

        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0

        picture_urls = [tag['src'] for tag in soup.find('div',
                        'woocommerce-product-gallery').findAll('img')]
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
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,

        )
        return [p]
