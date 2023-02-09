from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Multicenter(Store):
    base_url = 'https://www.multicenter.com.bo'

    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 25:
                raise Exception('Page overflow')

            url_webpage = '{}/lg?_q=lg&map=ft&page={}'.format(
                cls.base_url, page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')

            product_containers = soup.findAll(
                'section', 'vtex-product-summary-2-x-container')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category')
                break
            for container in product_containers:
                product_urls.append(cls.base_url + container.find('a')['href'])
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)

        key = json_data['mpn']
        name = json_data['name']
        sku = json_data['sku']
        price = Decimal(str(json_data['offers']['offers'][0]['price']))

        if soup.find('div', 'vtex-add-to-cart-button-0-x-buttonDataContainer'):
            stock = -1
        else:
            stock = 0

        picture_container = soup.findAll('div', 'swiper-container')[-1]
        picture_urls = []
        for i in picture_container.findAll('img'):
            picture_urls.append(i['src'])

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
            'BOB',
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
