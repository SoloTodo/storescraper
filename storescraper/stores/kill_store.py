import json
import re

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, MONITOR, MEMORY_CARD
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown
from decimal import Decimal


class KillStore(StoreWithUrlExtensions):
    url_extensions = [
        ['componentes-computacion', MOTHERBOARD],
        ['computacion', MOTHERBOARD],
        ['monitores-computacion', MONITOR],
        ['tarjetas-de-memoria-almacenamiento-fotografia', MEMORY_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 50:
                raise Exception('page overflow: ' + url_extension)

            url_webpage = ('https://www.killstore.cl/collections/{}'
                           '?page={}').format(url_extension, page)
            print(url_webpage)

            res = session.get(url_webpage)
            match = re.search(r'window.ORDERSIFY_BIS.collection_products = '
                              r'window.ORDERSIFY_BIS.collection_products \|\| '
                              r'(.+);', res.text)
            json_data = json.loads(match.groups()[0])

            if not json_data:
                break

            for product_entry in json_data:
                product_url = ('https://killstore.cl/products/' +
                               product_entry['handle'])
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        match = re.search(r'window.ORDERSIFY_BIS.product = '
                          r'window.ORDERSIFY_BIS.product \|\| '
                          r'(.+);', response.text)
        json_data = json.loads(match.groups()[0])

        variants = json_data['variants']
        assert len(variants) == 1
        variant = variants[0]
        name = variant['name']
        key = str(variant['id'])
        stock = -1 if variant['available'] else 0
        reference_price = Decimal(variant['price'] / 100)
        offer_price = (reference_price * Decimal('0.92')).quantize(0)
        normal_price = Decimal(remove_words(
            soup.find('span', 'price-custom').text))
        sku = variant['sku']
        picture_urls = ['https:' + x for x in json_data['images']]
        description = html_to_markdown(json_data['description'])

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
