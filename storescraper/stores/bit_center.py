import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, KEYBOARD, HEADPHONES, \
    STEREO_SYSTEM, VIDEO_CARD, COMPUTER_CASE, POWER_SUPPLY, GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class BitCenter(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            STEREO_SYSTEM,
            VIDEO_CARD,
            COMPUTER_CASE,
            POWER_SUPPLY,
            GAMING_CHAIR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['mouse', MOUSE],
            ['teclados', KEYBOARD],
            ['headsets', HEADPHONES],
            ['parlantes', STEREO_SYSTEM],
            ['tarjetas-de-video', VIDEO_CARD],
            ['gabinetes-pc', COMPUTER_CASE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['sillas-gamer', GAMING_CHAIR],
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
                url_webpage = 'https://www.bitcenter.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.find('ul', {
                    'data-hook': 'product-list-wrapper'})
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('li'):
                    product_url = container.find('a')['href']

                    if product_url in product_urls:
                        return product_urls

                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_container = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)

        if 'sku' not in json_container:
            return []

        sku = json_container['sku']
        name = json_container['name']

        if json_container['Offers']['Availability'] == 'https://schema.org/' \
                                                       'OutOfStock':
            stock = 0
        else:
            stock = -1
        normal_price = Decimal(
            int(json_container['Offers']['price']) * 1.038 // 1)
        offer_price = Decimal(json_container['Offers']['price'])
        picture_urls = [json_container['image']['contentUrl']]
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
