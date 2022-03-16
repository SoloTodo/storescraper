import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import POWER_SUPPLY, COMPUTER_CASE, MOTHERBOARD, \
    CPU_COOLER, HEADPHONES, MOUSE, STEREO_SYSTEM, SOLID_STATE_DRIVE, RAM, \
    MONITOR, KEYBOARD, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class JeanfigPc(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOTHERBOARD,
            CPU_COOLER,
            HEADPHONES,
            MOUSE,
            STEREO_SYSTEM,
            SOLID_STATE_DRIVE,
            RAM,
            MONITOR,
            KEYBOARD,
            VIDEO_CARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes/discos-de-estado-solido', SOLID_STATE_DRIVE],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/gabinetes', COMPUTER_CASE],
            ['componentes/memorias', RAM],
            ['componentes/placas-madres', MOTHERBOARD],
            ['componentes/ventiladores', CPU_COOLER],
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['monitores', MONITOR],
            ['perifericos/audifonos', HEADPHONES],
            ['perifericos/mouse', MOUSE],
            ['perifericos/parlantes-pc', STEREO_SYSTEM],
            ['perifericos/teclados', KEYBOARD],
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
                url_webpage = 'https://jeanfigpc.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage, verify=False).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'row list-product-row')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers. \
                        findAll('div', 'product-container'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_data = \
            json.loads(soup.findAll(
                'script', {'type': 'application/ld+json'})[1].text)[
                '@graph'][1]

        name = product_data['name']
        sku = str(product_data['sku'])
        normal_price = Decimal(product_data['offers'][0]['price'])
        offer_price = (normal_price * Decimal('0.95')).quantize(0)

        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        else:
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])

        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]

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
