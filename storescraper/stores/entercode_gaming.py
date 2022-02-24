import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, COMPUTER_CASE, MONITOR, \
    MOUSE, MOTHERBOARD, PROCESSOR, VIDEO_CARD, KEYBOARD, GAMING_CHAIR, \
    CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class EntercodeGaming(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            COMPUTER_CASE,
            MONITOR,
            MOUSE,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            KEYBOARD,
            GAMING_CHAIR,
            CPU_COOLER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos-headset', HEADPHONES],
            ['gabinetes', COMPUTER_CASE],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['placa-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['teclados', KEYBOARD],
            ['sillas-gamer', GAMING_CHAIR],
            ['refrigeracion', CPU_COOLER],
        ]
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) ' \
            'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.149 ' \
            'Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://entercodegaming.cl/categoria' \
                              '-producto/{}/page/{}/'.format(url_extension,
                                                             page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('a', 'product-content-image')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
                    if product_url not in product_urls:
                        product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) ' \
            'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.149 ' \
            'Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        part_number = None

        if not soup.find('script', {'type': 'application/ld+json'}):
            return []

        json_container = json.loads(
            soup.find('script',
                      {'type': 'application/ld+json'}).text)

        if '@graph' not in json_container:
            return []

        json_container = json_container['@graph'][1]
        name = json_container['name']

        if type(json_container['sku']) == str:
            part_number = json_container['sku']
            name += ' - ' + part_number

        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[1]\
            .strip()
        normal_price = Decimal(
            round(int(json_container['offers'][0]['price']) * 1.04))
        offer_price = Decimal(int(json_container['offers'][0]['price']))
        stock_tag = soup.find('div', 'product-information-inner')\
            .find('p', 'step-1') or \
            soup.find('div', 'product-information-inner')\
            .find('p', 'step-2')

        if stock_tag:
            stock = int(stock_tag.text.split()[0])
        else:
            stock = 0

        picture_urls = [tag['href'].split('?')[0] for tag in
                        soup.findAll('a', 'woocommerce-main-image')]
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
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
