from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import MONITOR, PROCESSOR, STEREO_SYSTEM, \
    VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TodoGeek(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            VIDEO_CARD,
            MONITOR,
            STEREO_SYSTEM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['cpus', PROCESSOR],
            ['tarjetas-graficas', VIDEO_CARD],
            ['monitores', MONITOR],
            ['parlantes-inteligentes', STEREO_SYSTEM],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://todogeek.cl/collections/{}?' \
                              'page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-grid-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find(
                        'h5', 'product-name').find('a')['href']
                    product_urls.append('https://todogeek.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        json_container = json.loads(
            "{" +
            re.search(r"var meta = \{([\s\S]*)\};\nfor", soup.text).groups()[0]
            + "}")['product']

        picture_urls = []
        picture_container = soup.find('div', 'slider-main-image')
        for picture in picture_container.findAll('div', 'slick-slide'):
            picture_urls.append(picture.find('a')['href'])

        products = []
        for variant in json_container['variants']:
            key = str(variant['id'])
            name = variant['name']
            price = (Decimal(variant['price']) /
                     Decimal(100)).quantize(Decimal("0.0"))

            if soup.find('button', 'add-to-cart'):
                stock = -1
            else:
                stock = 0

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
                picture_urls=picture_urls
            )
            products.append(p)
        return products
