import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, KEYBOARD, MOUSE, \
    HEADPHONES, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class DigiPlanet(Store):
    @classmethod
    def categories(cls):
        return [
            GAMING_CHAIR,
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            VIDEO_GAME_CONSOLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['sillas-gamer', GAMING_CHAIR],
            ['consolas', VIDEO_GAME_CONSOLE],
            ['teclados-gamer', KEYBOARD],
            ['mouses-gamer', MOUSE],
            ['audifonos-gamer', HEADPHONES]
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

                url_webpage = 'https://digiplanet.cl/collections/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('a', 'grid-view-item__link')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
                    product_urls.append('https://digiplanet.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.find(
            'script', {'id': 'ProductJson-product-template'}).text)
        sku = str(json_data['id'])
        name = json_data['title']
        description = html_to_markdown(json_data['description'])
        picture_urls = ['https:' + tag.split('?v')[0]
                        for tag in json_data['images']]
        products = []

        for variant in json_data['variants']:
            key = str(variant['id'])
            price = Decimal(variant['price'] / 100)
            stock = -1 if variant['available'] else 0

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

            products.append(p)

        return products
