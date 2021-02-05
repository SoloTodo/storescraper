import json
import logging

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, COMPUTER_CASE, \
    SOLID_STATE_DRIVE, RAM, MONITOR, MOUSE, GAMING_CHAIR, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class CrazyGamesenChile(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            COMPUTER_CASE,
            SOLID_STATE_DRIVE,
            RAM,
            MONITOR,
            MOUSE,
            GAMING_CHAIR,
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['audifonos-ps4-xbox-one-y-switch', HEADPHONES],
            ['gabinetes-gamer', COMPUTER_CASE],
            ['gabinetes-pc', COMPUTER_CASE],
            ['memorias-pendrives-disco-duro', SOLID_STATE_DRIVE],
            ['memorias-ram', RAM],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['mouse-ps4-xbox-one', MOUSE],
            ['sillas-gamer', GAMING_CHAIR],
            ['teclados', KEYBOARD],
            ['teclados-ps4-y-xbox-one', KEYBOARD]
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
                url_webpage = 'https://www.crazygamesenchile.com/{}?page={}' \
                    .format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', {
                    'data-hook': 'product-list-grid-item'})
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                if len(product_containers) == len(product_urls):
                    return product_urls
                product_containers = product_containers[len(product_urls):len(
                    product_containers) + 1]
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
        import ipdb
        ipdb.set_trace()
        json_container = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        name = json_container['name']
        sku = soup.find()
        if json_container['Offers'][
                'Availability'] == 'https://schema.org/OutOfStock':
            stock = 0
        else:
            stock = -1
        price = json_container['Offers']['price']
        picture_urls = [tag['src'] for tag in
                        soup.findAll('img', {'data-hook': 'thumbnail-image'})]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
