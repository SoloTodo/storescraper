import json
import re
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Panafoto(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'OpticalDiskPlayer',
            'Cell',
            'Refrigerator',
            'Oven',
            'Monitor',
            'Projector',
            'AirConditioner',
            'VacuumCleaner',
            'WashingMachine',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        endpoint = 'https://wlt832ea3j-dsn.algolia.net/1/indexes/*/queries?' \
                   'x-algolia-agent=Algolia%20for%20vanilla%20' \
                   'JavaScript%20(lite)%203.27.0%3Binstantsearch.js%20' \
                   '2.10.2%3BMagento2%20integration%20(1.10.0)%3BJS%20' \
                   'Helper%202.26.0&x-algolia-application-id=WLT832EA3J&x-alg'\
                   'olia-api-key=NzQyZDYyYTYwZGRiZDBjNjg0YjJmZDEyNWMyMTAyNTNh'\
                   'MjBjMDJiNzBhY2YyZWVjYWNjNzVjNjU5M2M5ZmVhY3RhZ0ZpbHRlcnM9'

        category_filters = [
            ('["categories.level2:Categorías /// TV y Video /// Televisores"]',
             'Television'),
            ('["categories.level3:Categorías /// TV y Video /// '
             'Reproductores de Audio y Video /// Barras de Sonido"]',
             'StereoSystem'),
            # ('["categories.level3:Categorías /// TV y Video /// '
            #  'Reproductores de Audio y Video /// Teatro en Casa"]',
            # 'StereoSystem'),
            # ('["categories.level3:Categorías /// TV y Video /// '
            #  'Reproductores de Audio y Video /// DVD / Blu-Ray"]',
            #  'OpticalDiskPlayer'),
            ('["categories.level3:Categorías /// Audio /// Bocinas /// '
             'Bocinas Bluetooth"]', 'StereoSystem'),
            # ('["categories.level3:Categorías /// Audio /// Sistemas de Audio'
            #  ' /// Equipos de Sonido"]', 'StereoSystem'),
            ('["categories.level2:Categorías /// Celulares y Tablets /// '
             'Celulares"]', 'Cell'),
            ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
             '/// Lavadoras"]', 'WashingMachine'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Lavadora Carga Superior"]', 'WashingMachine'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Lavadoras Semiautomáticas"]', 'WashingMachine'),
            ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
             '/// Secadoras"]', 'WashingMachine'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Secadora Gas"]', 'WashingMachine'),
            ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
             '/// Centros de Lavado"]', 'WashingMachine'),
            ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
             '/// Refrigeradoras"]', 'Refrigerator'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Refrigeradora Side by Side"]', 'Refrigerator'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Refrigeradora French-Door"]', 'Refrigerator'),
            ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
             '/// Congeladores"]', 'Refrigerator'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Minibares y Vineras"]', 'Refrigerator'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Aires portátiles"]', 'AirConditioner'),
            ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
             '/// Aires Acondicionados"]', 'AirConditioner'),
            ('["categories.level3:Categorías /// Cómputo /// Monitores '
             '/// Monitores"]', 'Monitor'),
            ('["categories.level3:Categorías /// Cómputo /// Proyectores '
             '/// Proyectores"]', 'Projector'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Hornos a gas"]', 'Oven'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Hornos eléctricos"]', 'Oven'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Estufas eléctricas"]', 'Stove'),
            # ('["categories.level3:Categorías /// Hogar /// Línea Blanca '
            #  '/// Estufas a Gas"]', 'Stove'),
            ('["categories.level3:Categorías /// Hogar /// Electrodomésticos '
             '/// Aspiradoras"]', 'VacuumCleaner'),
            ('["categories.level3:Categorías /// Hogar /// Electrodomésticos '
             '/// Aspiradoras"]', 'VacuumCleaner'),
            ('["categories.level3:Categorías /// Hogar /// Electrodomésticos '
             '/// Microondas"]', 'Oven'),
        ]

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        session.headers['Referer'] = 'https://www.panafoto.com/'

        product_urls = []

        for category_filter, local_category in category_filters:
            if local_category != category:
                continue

            page = 0

            while True:
                payload_params = "page={}&facetFilters={}&numericFilters=%5B" \
                                 "%22visibility_catalog%3D1%22%5D" \
                                 "".format(page, urllib.parse.quote(
                                    category_filter).replace('/', '%2F'))

                payload = {"requests": [
                    {"indexName": "wwwpanafotocom_default_products",
                     "params": payload_params}]}

                response = session.post(endpoint, data=json.dumps(payload))
                products_json = json.loads(response.text)['results'][0]['hits']

                if not products_json:
                    if page == 0:
                        raise Exception('Empty category: ' + category_filter)
                    break

                for product_json in products_json:
                    if 'LG' not in product_json['manufacturer']:
                        continue
                    product_url = product_json['url']
                    if isinstance(product_url, list):
                        product_url = ','.join(product_url)

                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        data = response.text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('form', {'id': 'product_addtocart_form'})[
            'data-product-sku']

        part_number_match = re.search(
            r"ccs_cc_args.push\(\['pn', '(.+)'\]\);", data)

        if part_number_match:
            part_number = part_number_match.groups()[0]
        else:
            part_number = None

        if soup.find('div', 'unavailable'):
            stock = 0
        else:
            stock = -1

        price_text = soup.find('meta',
                               {'property': 'product:price:amount'})['content']
        price = Decimal(price_text)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'description'})))

        pictures_tag = None

        for tag in soup.findAll('script', {'type': 'text/x-magento-init'}):
            if 'data-gallery-role=gallery-placeholder' in tag.text:
                pictures_tag = tag
                break

        pictures = json.loads(pictures_tag.text)[
            '[data-gallery-role=gallery-placeholder]'][
            'mage/gallery/gallery']['data']

        picture_urls = [e['full'] for e in pictures]

        variants_tag = soup.find('select', 'product-custom-option')

        if variants_tag:
            suffixes = [' ' + tag.text.strip() for tag in
                        variants_tag.findAll('option')[1:]]
        else:
            suffixes = ['']

        products = []

        for suffix in suffixes:
            products.append(Product(
                name + suffix,
                cls.__name__,
                category,
                url,
                url,
                sku + suffix,
                stock,
                price,
                price,
                'USD',
                sku=sku,
                part_number=part_number,
                description=description,
                picture_urls=picture_urls
            ))

        return products
