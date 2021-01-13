import json
import re
from collections import defaultdict
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class Jumbo(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Refrigerator',
            'WashingMachine',
            'Oven',
            'Printer',
            'MemoryCard',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'Headphones',
            'StereoSystem',
            'Television',
            'Mouse'
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['electro-y-tecnologia/tecnologia/celulares', ['Cell'],
             'Electro y Tecnología > Teconología > Celulares', 1],
            ['electro-y-tecnologia/tecnologia/almacenamiento', ['MemoryCard'],
             'Electro y Tecnología > Tecnología > Almacenamiento', 1],
            ['electro-y-tecnologia/tecnologia/audifonos', ['Headphones'],
             'Electro y Tecnología > Tecnología > Audífonos', 1],
            ['electro-y-tecnologia/tecnologia/impresoras', ['Printer'],
             'Electro y Tecnología > Tecnología > Impresoras', 1],
            ['electro-y-tecnologia/electronica/equipos-de-musica',
             ['StereoSystem'],
             'Electro y Tecnología > Electrónica > Equipos de Música', 1],
            ['electro-y-tecnologia/electronica/parlantes', ['StereoSystem'],
             'Electro y Tecnología > Electrónica > Parlantes', 1],
            ['electro-y-tecnologia/electronica/televisores', ['Television'],
             'Electro y Tecnología > Electrónica > Televisores', 1],
            ['electro-y-tecnologia/electrohogar/cocina-y-microondas', ['Oven'],
             'Electro y Tecnología > Electrohogar > Cocina y Microondas', 1],
        ]

        session = session_with_proxy(extra_args)
        session.headers['x-api-key'] = 'IuimuMneIKJd3tapno2Ag1c1WcAES97j'
        product_entries = defaultdict(lambda: [])

        for url_extension, local_categories, section_name, category_weight in \
                url_extensions:

            if category not in local_categories:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + url_extension)

                api_url = 'https://api.smdigital.cl:8443/v0/cl/jumbo/vtex/' \
                          'front/prod/proxy/api/v2/products/search/{}?page={}' \
                    .format(url_extension, page)

                json_data = json.loads(session.get(api_url).text)

                if not json_data:
                    break

                for idx, product in enumerate(json_data):
                    product_url = 'https://www.jumbo.cl/{}/p' \
                        .format(product['linkText'])

                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': 40 * (page - 1) + idx + 1
                    })

                page += 1

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_container = json.loads(
            soup.findAll('script', {'type': 'application/ld+json'})[1].text)
        name = product_container['name']
        sku = soup.find('span', 'product-code').text.split()[1]
        price = Decimal(product_container['offers']['price'])

        pictures_tag = soup.find('ul', 'product-image-thumbs-list')

        if pictures_tag:
            picture_urls = [tag['src'].split('?')[0] for tag in
                            pictures_tag.findAll('img')]
        else:
            picture_urls = None

        if soup.find('meta', {'property': 'product:availability'})[
            'content'] == 'out of stock':
            stock = 0
        else:
            stock = -1

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
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
        )

        return [p]
