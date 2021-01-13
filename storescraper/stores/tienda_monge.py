import json
import logging
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import CELL, TELEVISION, OPTICAL_DISK_PLAYER, \
    AIR_CONDITIONER, STOVE, OVEN, WASHING_MACHINE, REFRIGERATOR, \
    STEREO_SYSTEM, MONITOR, HEADPHONES


class TiendaMonge(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            TELEVISION,
            OPTICAL_DISK_PLAYER,
            AIR_CONDITIONER,
            STOVE,
            OVEN,
            WASHING_MACHINE,
            REFRIGERATOR,
            STEREO_SYSTEM,
            MONITOR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # KEEPS ONLY LG PRODUCTS

        endpoint = 'https://wlt832ea3j-dsn.algolia.net/1/indexes/*/queries?' \
                   'x-algolia-agent=Algolia%20for%20vanilla%20' \
                   'JavaScript%20(lite)%203.27.0%3Binstantsearch.js%20' \
                   '2.10.2%3BMagento2%20integration%20(1.13.0)%3BJS%20' \
                   'Helper%202.26.0&x-algolia-application-id=WLT832EA3J&x-al' \
                   'golia-api-key=MjQyMGI4YWYzNWJkNzg5OTIxMmRkYTljY2ZmNDkyOD' \
                   'NmMmZmNGU1NWRkZWU3NGE3MjNhYmNmZWZhOWFmNmQ0M3RhZ0ZpbHRlcnM9'

        category_filters = [
            ('["categories.level2:Productos /// Celulares y Tablets '
             '/// Celulares"]',
             CELL),
            ('["categories.level2:Productos /// TV y Video /// Pantallas"]',
             TELEVISION),
            ('["categories.level2:Productos /// TV y Video /// '
             'Reproductores de video y proyectores"]',
             OPTICAL_DISK_PLAYER),
            ('["categories.level2:Productos /// Hogar /// '
             'Aires acondicionados"]',
             AIR_CONDITIONER),
            ('["categories.level2:Productos /// Hogar /// Cocinas"]',
             STOVE),
            ('["categories.level2:Productos /// Hogar /// '
             'Hornos y extractores"]',
             OVEN),
            ('["categories.level2:Productos /// Hogar /// '
             'Lavadoras y secadoras"]',
             WASHING_MACHINE),
            ('["categories.level2:Productos /// Hogar /// Refrigeradoras"]',
             REFRIGERATOR),
            ('["categories.level2:Productos /// Audio /// Minicomponentes"]',
             STEREO_SYSTEM),
            ('["categories.level2:Productos /// Audio /// Parlantes"]',
             STEREO_SYSTEM),
            ('["categories.level2:Productos /// Audio /// '
             'Sistemas de audio y accesorios"]',
             STEREO_SYSTEM),
            ('["categories.level2:Productos /// Computadoras /// '
             'De Escritorio"]',
             MONITOR),
            ('["categories.level2:Productos /// Audio /// Audífonos"]',
             HEADPHONES),
        ]

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'
        product_urls = []

        for category_id, local_category in category_filters:
            if local_category != category:
                continue

            payload_params = 'hitsPerPage=1000&page=0&facetFilters={}'.format(
                urllib.parse.quote(category_id).replace('/', '%2F')
            )

            payload = {
                "requests": [
                    {"indexName": "monge_prod_default_products",
                     "params": payload_params}
                ]
            }

            response = session.post(endpoint, data=json.dumps(payload))
            products_json = json.loads(response.text)['results'][0]['hits']

            if not products_json:
                logging.warning('Empty category: ' + category_id)

            for product in products_json:
                if product.get('marca', None) == 'LG':
                    product_urls.append(product['url'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name_container = soup.find('span', {'data-ui-id': 'page-title-wrapper'})

        if not name_container:
            return []

        name = name_container.text.strip()
        sku = soup.find('div', 'value').text.strip()

        if soup.find('button', {'id': 'product-addtocart-button'}):
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('span', 'price').text
                        .replace('₡', '').replace('.', '').strip())

        picture_urls = [soup.find('img', {'alt': 'main product photo'})['src']]

        description = html_to_markdown(
            str(soup.find('div', 'product attribute description'))
        )

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
            'CRC',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
