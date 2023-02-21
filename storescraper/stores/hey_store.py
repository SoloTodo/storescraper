from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import COMPUTER_CASE, EXTERNAL_STORAGE_DRIVE, \
    HEADPHONES, KEYBOARD, MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, \
    POWER_SUPPLY, PROCESSOR, RAM, SOLID_STATE_DRIVE, STEREO_SYSTEM, \
    STORAGE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class HeyStore(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            COMPUTER_CASE,
            POWER_SUPPLY,
            KEYBOARD,
            MOUSE,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            MONITOR,
            HEADPHONES,
            STEREO_SYSTEM,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebooks', NOTEBOOK],
            ['procesadores-intel', PROCESSOR],
            ['procesadores-amd', PROCESSOR],
            ['placas-madre-intel', MOTHERBOARD],
            ['placas-madre-amd', MOTHERBOARD],
            ['memorias-ram-pc', RAM],
            ['memorias-ram-notebook', RAM],
            ['gabinetes', COMPUTER_CASE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['discos-externos', EXTERNAL_STORAGE_DRIVE],
            ['discos-duros-pc', STORAGE_DRIVE],
            ['discos-ssd', SOLID_STATE_DRIVE],
            ['discos-m-2', SOLID_STATE_DRIVE],
            ['discos-nas', STORAGE_DRIVE],
            ['monitores', MONITOR],
            ['audifonos', HEADPHONES],
            ['parlante', STEREO_SYSTEM],
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

                url_webpage = 'https://heystore.cl/collections/{}?page={}' \
                    ''.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'grid__item')

                if len(product_containers) == 0:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://heystore.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('input', {'name': 'id'})['value']

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        name = json_data['name']
        description = json_data['description']
        sku = json_data.get('sku', None)

        price = Decimal(str(json_data['offers'][0]['price']))

        if price == Decimal(0):
            return []

        add_to_cart = soup.find('button', 'product-form__submit')
        if 'disabled' not in add_to_cart.attrs:
            stock = -1
        else:
            stock = 0

        picture_container = soup.find('ul', 'product__media-list')
        picture_urls = []
        for i in picture_container.findAll('img'):
            picture_urls.append('https:' + i['src'])

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
            description=description,
        )
        return [p]
