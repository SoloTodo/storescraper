import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, KEYBOARD, HEADPHONES, \
    STEREO_SYSTEM, VIDEO_CARD, COMPUTER_CASE, POWER_SUPPLY, GAMING_CHAIR, \
    MOTHERBOARD, CPU_COOLER, MICROPHONE
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
            MOTHERBOARD,
            CPU_COOLER,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['mouse', MOUSE],
            ['teclados', KEYBOARD],
            ['headset', HEADPHONES],
            ['parlantes', STEREO_SYSTEM],
            ['componentes-pc/placa-madre', MOTHERBOARD],
            ['componentes-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-pc/gabinetes', COMPUTER_CASE],
            ['componentes-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-pc/refrigeracion', CPU_COOLER],
            ['sillas-gamer', GAMING_CHAIR],
            ['microfonos', MICROPHONE]
        ]
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.bitcenter.cl/categoria/{}?page={}' \
                    .format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('main', 'site-main'). \
                    find('ul', 'products')

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
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_container = \
            json.loads(soup.findAll(
                'script', {'type': 'application/ld+json'})[1].text)[
                '@graph'][1]
        name = json_container['name']
        sku = json_container['sku']

        stock_tag = soup.find('input', {'name': 'quantity'})
        if stock_tag:
            if 'max' in stock_tag.attrs:
                stock = int(stock_tag['max'])
            else:
                stock = 1
        else:
            stock = 0

        normal_price = Decimal(
            int(json_container['offers'][0]['price']) * 1.038 // 1)
        offer_price = Decimal(json_container['offers'][0]['price'])
        picture_urls = [json_container['image']]

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
        )
        return [p]
