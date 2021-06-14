import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, KEYBOARD, HEADPHONES, \
    GAMING_CHAIR, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class HouseOfGamers(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            GAMING_CHAIR,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['mouse', MOUSE],
            ['teclados', KEYBOARD],
            ['audifonos', HEADPHONES],
            ['sillas', GAMING_CHAIR],
            ['monitores', MONITOR]
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

                url_webpage = 'https://houseofgamers.cl/collections/{}' \
                              '?page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-wrap')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://houseofgamers.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_container = json.loads(
            soup.find('div', 'product_form')['data-product'])
        name = json_container['variants'][0]['name']
        sku = str(json_container['variants'][0]['id'])
        part_number = json_container['variants'][0]['sku']
        if soup.find('span', 'sold_out').text == 'Agotado':
            stock = 0
        elif soup.find('div', 'items_left').text == '':
            stock = -1
        else:
            stock = int(soup.find('div', 'items_left').text.strip().split()[0])
        price = Decimal(
            remove_words(soup.find('span', 'current_price').text.strip()))
        picture_urls = ['https:' + tag.split('?v=')[0] for tag in
                        json_container['images']]
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
            part_number=part_number,
            picture_urls=picture_urls,
        )
        return [p]
