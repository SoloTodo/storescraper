from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, SOLID_STATE_DRIVE, \
    HEADPHONES, MOTHERBOARD, PROCESSOR, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Campcom(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE, SOLID_STATE_DRIVE, HEADPHONES, MOTHERBOARD, PROCESSOR,
            VIDEO_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('componentes', MOUSE),
            ('disco-solido-ssd', SOLID_STATE_DRIVE),
            ('mouse', MOUSE),
            ('perifericos', HEADPHONES),
            ('placas-madre', MOTHERBOARD),
            ('procesadores', PROCESSOR),
            ('tarjetas-de-video', VIDEO_CARD),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + category_path)
                url_webpage = 'https://campcom.cl/categoria-producto/{}/' \
                              'page/{}/'.format(category_path, page)
                print(url_webpage)
                response = session.get(url_webpage)

                if response.status_code == 404:
                    if page == 1:
                        logging.warning('Empty category: ' + url_webpage)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'type-product')

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

        if 'Error 404: Página no encontrada' in soup.text:
            return []

        key = soup.find('link', {'rel': 'shortlink'})[
            'href'].split('=')[-1]
        soup_json = soup.findAll(
            'script', {'type': 'application/ld+json'})

        json_data = json.loads(soup_json[-1].text)

        if 'name' not in json_data:
            return []

        name = json_data['name']
        sku = str(json_data['sku'])
        offer = json_data['offers'][0]
        if 'price' in offer:
            offer_price = Decimal(offer['price'])
        else:
            offer_price = Decimal(offer['lowPrice'])
        normal_price = (offer_price * Decimal('1.04')).quantize(0)
        stock_span = soup.find('span', 'stock in-stock')

        if soup.find('p', 'available-on-backorder') or \
                soup.find('p', 'stock out-of-stock'):
            stock = 0
        elif stock_span:
            stock = int(stock_span.text.split('disp')[0].strip())
        else:
            stock = -1

        picture_urls = []
        picture_container = soup.find(
            'div', 'woocommerce-product-gallery__wrapper')
        for a in picture_container.findAll('a'):
            if a['href'] != "":
                picture_urls.append(a['href'])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )

        return [p]
