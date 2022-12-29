from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import MONITOR, PROCESSOR, STEREO_SYSTEM, \
    VIDEO_CARD, NOTEBOOK, GAMING_CHAIR, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TodoGeek(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            VIDEO_CARD,
            MONITOR,
            STEREO_SYSTEM,
            NOTEBOOK,
            GAMING_CHAIR,
            WEARABLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['cpus', PROCESSOR],
            ['tarjetas-graficas', VIDEO_CARD],
            ['monitores', MONITOR],
            ['parlantes-inteligentes', STEREO_SYSTEM],
            ['laptops-computer', NOTEBOOK],
            ['sillas-gamer', GAMING_CHAIR],
            ['watches', WEARABLE],
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
        match = re.search('product: (.+), onVariantSelected', response.text)
        json_data = json.loads(match.groups()[0])

        picture_urls = []

        for picture in json_data['images']:
            picture_urls.append('https:' + picture)

        description = html_to_markdown(json_data['description'])

        products = []
        for variant in json_data['variants']:
            key = str(variant['id'])
            name = variant['name']
            price = (Decimal(variant['price']) /
                     Decimal(100)).quantize(0)

            if 'RESERVA' in description.upper():
                stock = 0
            elif variant['available']:
                stock = -1
            else:
                stock = 0

            if 'OPEN BOX' in name.upper() or 'OPEN BOX' in description.upper():
                condition = 'https://schema.org/OpenBoxCondition'
            else:
                condition = 'https://schema.org/NewCondition'

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
                picture_urls=picture_urls,
                description=description,
                condition=condition
            )
            products.append(p)
        return products
