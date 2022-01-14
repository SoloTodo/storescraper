import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import POWER_SUPPLY, MONITOR, PROCESSOR, \
    SOLID_STATE_DRIVE, VIDEO_CARD, MOTHERBOARD, CPU_COOLER, NOTEBOOK, RAM, \
    COMPUTER_CASE, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class DazbogStore(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            MONITOR,
            PROCESSOR,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            MOTHERBOARD,
            CPU_COOLER,
            NOTEBOOK,
            RAM,
            COMPUTER_CASE,
            KEYBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['cooler-cpu', CPU_COOLER],
            ['psu', POWER_SUPPLY],
            ['monitores', MONITOR],
            ['notebooks-gamer', NOTEBOOK],
            ['placas-madre', MOTHERBOARD],
            ['cpu', PROCESSOR],
            ['ram', RAM],
            ['ssd', SOLID_STATE_DRIVE],
            ['gpus', VIDEO_CARD],
            ['gabinete', COMPUTER_CASE],
            ['perifericos', KEYBOARD],
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
                url_webpage = 'https://www.dazbogstore.cl/product-category' \
                              '/{}/page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('div',
                                                            'col-inner'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text.strip()
        part_number = None
        part_number_tag = soup.find('span', 'sku')

        if part_number_tag:
            part_number = part_number_tag.text.strip()
            name += ' - ' + part_number

        sku = str(soup.find('button', 'single_add_to_cart_button')['value'])
        stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        price_container = soup.find('table').findAll('bdi')
        offer_price = Decimal(remove_words(price_container[0].text))
        normal_price = Decimal(remove_words(price_container[1].text))
        picture_urls = [
            soup.find('div', 'woocommerce-product-gallery__image').find('img')[
                'data-large_image']]
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
            picture_urls=picture_urls,
            part_number=part_number
        )

        return [p]
