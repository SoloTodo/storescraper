from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MONITOR, MOTHERBOARD, MOUSE, \
    POWER_SUPPLY, PROCESSOR, RAM, STORAGE_DRIVE, STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class BiosPlay(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            HEADPHONES,
            POWER_SUPPLY,
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            MOUSE,
            STEREO_SYSTEM,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['discos-duros', STORAGE_DRIVE],
            ['audifonos', HEADPHONES],
            ['fuente-de-poder', POWER_SUPPLY],
            ['memorias-ram', RAM],
            ['monitores-gamer', MONITOR],
            ['mouse', MOUSE],
            ['parlantes', STEREO_SYSTEM],
            ['placa-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['zona-gamer', MOUSE],
            ['zona-oficina', MOUSE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.biosplay.cl/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.biosplay.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('form', {'name': 'buy'})['action'].split('/')[-1]

        json_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)

        name = json_data['name']
        sku = json_data['sku']
        description = json_data['description']
        price = Decimal(json_data['offers']['price'])

        input_qty = soup.find('input', 'qty')
        if input_qty:
            if 'max' in input_qty.attrs and input_qty['max']:
                stock = int(input_qty['max'])
            else:
                stock = -1
        else:
            stock = 0

        picture_urls = []
        picture_container = soup.find('div', 'main-product-image')
        for image in picture_container.findAll('img'):
            picture_urls.append(image['src'])

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
            description=description
        )
        return [p]
