import json
from decimal import Decimal
import logging
import re
import time

from bs4 import BeautifulSoup

from storescraper.categories import WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Woow(Store):
    @classmethod
    def categories(cls):
        return [
            WASHING_MACHINE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extension = [
            WASHING_MACHINE
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extension:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow: ' + local_category)
                url_webpage = 'https://shop.tata.com.uy/lg/lg?_q=lg&fuzzy=0' \
                    '&initialMap=ft&initialQuery=lg&map=brand,ft&operator=a' \
                    'nd&page={}'.format(page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')

                if 'oops!' in soup.text:
                    if page == 1:
                        logging.warning('Empty category: ' + local_category)
                    break

                template = soup.find('template', {'data-varname': '__STATE__'})
                item_list = json.loads(template.text)
                for k in item_list.keys():
                    if 'linkText' in item_list[k]:
                        product = item_list[k]['linkText']
                        product_urls.append(
                            f"https://shop.tata.com.uy/{product}/p")

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        soup_jsons = soup.findAll(
            'script', {'type': 'application/ld+json'})
        if len(soup_jsons) == 0 or not soup_jsons[0].text:
            return []
        json_data = json.loads(soup_jsons[0].text)
        name = json_data['name']
        sku = str(json_data['sku'])

        stock = 0
        if soup.find('div', 'vtex-add-to-cart-button-0-x-buttonDataContainer'):
            stock = -1

        price = Decimal(
            json_data['offers']['offers'][0]['price']
        )
        price = price.quantize(Decimal('0.01'))
        picture_urls = [tag['src'] for tag in
                        soup.find(
                            'div',
                            'vtex-store-components-3-x-'
                            'productImagesGallerySlide'
        ).findAll('img')
        ]
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
            'UYU',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
