import json
import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import POWER_SUPPLY, MOTHERBOARD, CPU_COOLER, \
    MONITOR, GAMING_CHAIR, VIDEO_CARD, HEADPHONES, COMPUTER_CASE, \
    KEYBOARD_MOUSE_COMBO, MOUSE, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class PlayFactory(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            MOTHERBOARD,
            CPU_COOLER,
            MONITOR,
            GAMING_CHAIR,
            VIDEO_CARD,
            HEADPHONES,
            COMPUTER_CASE,
            KEYBOARD_MOUSE_COMBO,
            MOUSE,
            KEYBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/placa-madre-componentes', MOTHERBOARD],
            ['componentes/refrigeracion', CPU_COOLER],
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['monitor', MONITOR],
            ['sillas-y-escritorios', GAMING_CHAIR],
            ['tarjeta-de-video', VIDEO_CARD],
            ['zona-gamer/audifonos', HEADPHONES],
            ['zona-gamer/gabinetes', COMPUTER_CASE],
            ['zona-gamer/kit-teclado-mouse-audifono', KEYBOARD_MOUSE_COMBO],
            ['zona-gamer/mouse', MOUSE],
            ['zona-gamer/teclados', KEYBOARD]
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
                url_webpage = 'https://www.playfactory.cl/categorias/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'products')
                if not product_containers or soup.find('div', 'info-404'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('li', 'product'):
                    product_url = container.find('a', 'woocommerce-Loop'
                                                      'Product-link')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if soup.find('figure', 'electro-wc-product-gallery__wrapper'):
            picture_urls = [tag['src'].replace('-100x100', '') for tag in
                            soup.find('figure', 'electro-wc-product-gallery'
                                                '__wrapper').findAll('img')]
        else:
            picture_urls = [soup.find('figure', 'woocommerce-product-gallery__'
                                                'wrapper').find('img')['src']]

        json_data = re.search('google_tag_params = (.+);', response.text)
        json_data = json.loads(json_data.groups()[0])
        products = []

        for product_entry in json_data['ecommerce']['detail']['products']:
            name = product_entry['name']
            sku = product_entry['sku']
            stock = product_entry['stocklevel']
            offer_price = Decimal(product_entry['price'])
            normal_price = (offer_price * Decimal('1.035')).quantize(0)

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
            products.append(p)

        return products
