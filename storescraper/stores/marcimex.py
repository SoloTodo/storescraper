import json
import logging

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper.categories import AIR_CONDITIONER, OVEN, WASHING_MACHINE, \
    REFRIGERATOR, STEREO_SYSTEM, TELEVISION


class Marcimex(Store):
    @classmethod
    def categories(cls):
        return [
            AIR_CONDITIONER,
            OVEN,
            WASHING_MACHINE,
            REFRIGERATOR,
            STEREO_SYSTEM,
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['lg', WASHING_MACHINE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                url = 'https://www.marcimex.com/{}?page={}'.format(
                    category_path, page)
                print(url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                products_container = soup.find(
                    'div', {'id': 'gallery-layout-container'})

                if not products_container:
                    if page == 1:
                        logging.warning('Empty url {}'.format(url))
                    break

                products = products_container.findAll(
                    'section', 'vtex-product-summary-2-x-container')

                for product in products:
                    product_url = product.find('a')['href']
                    product_urls.append(
                        'https://www.marcimex.com' + product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_json = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)

        name = product_json['name']
        sku = str(product_json['sku'])
        description = product_json['description']

        stock = int(
            soup.find('span',
                      'vtex-product-availability-0-x-lowStockHighlight').text)

        product_div = soup.find(
            'div', 'vtex-flex-layout-0-x-flexRow--quantity')
        product_price = product_div.find(
            'span', 'vtex-product-price-1-x-sellingPrice')

        price = Decimal(product_price.find(
            'span', 'vtex-product-price-1-x-currencyContainer')
            .text.replace('$', '').replace(',', '.'))

        picture_urls = []
        picture_container = soup.findAll('div', 'swiper-wrapper')[1]
        for i in picture_container.findAll('img'):
            picture_urls.append(i['src'])

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
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
