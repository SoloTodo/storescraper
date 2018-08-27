import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class RipleyPeru(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'http://simple.ripley.com.pe/{}?page={}&pageSize=50&' \
                   'orderBy=3'

        category_urls = [
            # ['computo/laptops/todas-las-laptops', 'Notebook'],
            # ['computo/2-en-1-convertibles/laptops-2-en-1', 'Notebook'],
            ['computo/almacenamiento/discos-duros', 'ExternalStorageDrive'],
            ['computo/almacenamiento/memorias-usb', 'UsbFlashDrive'],
            # ['celulares/accesorios/memorias', 'MemoryCard'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_url, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 20:
                    raise Exception()

                page_url = url_base.format(category_url, page)
                response = session.get(page_url)

                if not response.ok:
                    if page == 1:
                        raise Exception('Empty category: ' + page_url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                product_link_containers = soup.find(
                    'div', 'catalog-container')

                if not product_link_containers:
                    break

                product_link_containers = product_link_containers.findAll(
                    'a', 'catalog-item')

                for link_tag in product_link_containers:
                    product_url = 'http://simple.ripley.com.pe' + \
                                  link_tag['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        product_data = re.search(r'window.__PRELOADED_STATE__ = (.+);',
                                 page_source)
        product_json = json.loads(product_data.groups()[0])
        specs_json = product_json['product']['product']

        if 'name' not in specs_json:
            return []

        sku = specs_json['partNumber']
        if specs_json['isOutOfStock'] or specs_json['isUnavailable']:
            stock = 0
        else:
            stock = -1

        if 'offerPrice' in specs_json['prices']:
            normal_price = Decimal(specs_json['prices']['offerPrice'])
        elif 'listPrice' in specs_json['prices']:
            normal_price = Decimal(specs_json['prices']['listPrice'])
        else:
            return []

        offer_price = Decimal(specs_json['prices'].get('cardPrice',
                                                       normal_price))

        if offer_price > normal_price:
            offer_price = normal_price

        description = ''

        if 'longDescription' in specs_json:
            description += html_to_markdown(specs_json['longDescription'])

        description += '\n\nAtributo | Valor\n-- | --\n'

        for attribute in specs_json['attributes']:
            description += '{} | {}\n'.format(attribute['name'],
                                              attribute['value'])

        description += '\n\n'

        picture_urls = []
        for path in specs_json['images']:
            picture_url = path

            if not picture_url.startswith('https'):
                picture_url = 'https:' + picture_url

            picture_urls.append(picture_url)

        p = Product(
            specs_json['name'],
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'PEN',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
