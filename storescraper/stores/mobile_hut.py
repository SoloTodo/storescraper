import json
import re

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class MobileHut(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Headphones',
            'StereoSystem',
            'Mouse',
            'Keyboard',
            'Wearable',
            'UsbFlashDrive',
            'MemoryCard',
            'VideoGameConsole',
            'Monitor',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_urls = [
            ['89857884224', 'smartphones', 'Cell'],
            ['89858244672', 'audifonos', 'Headphones'],
            ['129582760000', 'audio-gamer', 'Headphones'],
            ['89858441280', 'parlantes', 'StereoSystem'],
            ['132833869888', 'mouses', 'Mouse'],
            ['129574076480', 'mouse-gamer', 'Mouse'],
            ['132834033728', 'teclados-1', 'Keyboard'],
            ['133205065792', 'smartwatch', 'Wearable'],
            # ['132830560320', 'pendrives', 'UsbFlashDrive'],
            ['132830593088', 'tarjetas-de-memoria', 'MemoryCard'],
            ['129583054912', 'consolas', 'VideoGameConsole'],
            ['206952595607', 'monitores', 'Monitor'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_id, category_name, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                api_url = 'https://services.mybcapps.com/bc-sf-filter/filter?'\
                          'shop=mobilehutcl.myshopify.com&' \
                          'page={}&limit=32&sort=best-selling&' \
                          'collection_scope={}'.format(page, category_id)

                products_data = json.loads(
                    session.get(api_url).text)['products']

                if not products_data and page == 1:
                    raise Exception('No products for collection {}'
                                    .format(category_name))
                if not products_data:
                    break

                for product in products_data:
                    product_url = 'https://mobilehut.cl/collections' \
                                  '/{}/products/{}'\
                        .format(category_name, product['handle'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response_text = session.get(url).text

        variants_raw_data = re.search(
            r'var meta = ([\S\s]+?);\n', response_text).groups()[0]
        variants_data = json.loads(variants_raw_data)['product']['variants']

        products = []

        for variant in variants_data:
            variant_id = variant['id']
            sku = variant['sku']
            color = variant['public_title']

            variant_url = '{}?variant={}'.format(url, variant_id)
            variant_url_source = session.get(variant_url).text
            soup = BeautifulSoup(variant_url_source, 'html.parser')
            name = soup.find('h1', 'product_name').text + " ({})".format(color)
            stock = 0

            if soup.find('link', {'itemprop': 'availability'})['href'] == \
                    'http://schema.org/InStock':
                stock = -1

            price = Decimal(soup.find('span', 'current_price')
                            .text.replace('$', '').replace('.', ''))

            image_containers = soup.findAll('div', 'image__container')
            picture_urls = ['http:' + i.find('img')['data-src']
                            for i in image_containers]

            description = html_to_markdown(
                str(soup.find('div', {'data-et-handle': 'tabs-descripcion'})))

            p = Product(
                name,
                cls.__name__,
                category,
                variant_url,
                url,
                sku,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls,
                description=description)

            products.append(p)

        return products
