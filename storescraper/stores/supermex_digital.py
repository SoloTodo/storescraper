import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    MOTHERBOARD, PROCESSOR, CPU_COOLER, RAM, VIDEO_CARD, POWER_SUPPLY, \
    COMPUTER_CASE, MOUSE, MONITOR, TABLET, NOTEBOOK


class SupermexDigital(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            RAM,
            VIDEO_CARD,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOUSE,
            MONITOR,
            TABLET,
            NOTEBOOK,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento-interno/disco-mecanico', STORAGE_DRIVE],
            ['almacenamiento-interno/disco-solido', SOLID_STATE_DRIVE],
            ['almacenamiento-interno/m2', SOLID_STATE_DRIVE],
            ['tarjetas-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['sistema-de-enfriamiento', CPU_COOLER],
            ['memoria-ram', RAM],
            ['tarjeta-de-video', VIDEO_CARD],
            ['fuente', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['mouse', MOUSE],
            ['monitores', MONITOR],
            ['tablet', TABLET],
            ['laptop', NOTEBOOK],

        ]

        base_url = 'https://www.supermexdigital.mx/collections/{}?page={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)
                print(url)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                product_container = soup.find('div',  'productgrid--items')
                products = product_container.findAll('div', 'productitem')

                if not products:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                for product in products:
                    product_url = 'https://www.supermexdigital.mx{}'\
                        .format(product.find('a')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        data = json.loads(
            soup.find('script', {'data-section-id': 'static-product'}).text)

        variants = data['product']['variants']

        picture_urls = soup.findAll('figure', 'product-gallery--image')
        picture_urls = ['https:{}'.format(i.find('img')['src'])
                        for i in picture_urls]
        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

        products = []

        for product in variants:
            name = product['name']
            sku = product['sku']
            stock = product['inventory_quantity']
            price = Decimal(product['price']/100)

            products.append(
                Product(
                    name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    stock,
                    price,
                    price,
                    'MXN',
                    sku=sku,
                    picture_urls=picture_urls,
                    description=description,
                )
            )

        return products
