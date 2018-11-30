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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        endpoint = 'https://s7a9hbqh8k-dsn.algolia.net/1/indexes/*/' \
                   'queries?x-algolia-application-id=S7A9HBQH8K&x-algolia-' \
                   'api-key=MTVmNjcxMDZjYjRhZDkyZjJkMGNjZTY5YTA2YzQwYzI4Y2Rj' \
                   'ZDdlMmUyNmI3NzMzNDM5MTdkMzgyYmZmMGUwMXRhZ0ZpbHRlcnM9'

        category_filters = [
            ('["categories.level2:Categorías /// TV y Video /// Televisores"]',
             'Television'),
            ('["categories.level2:Categorías /// TV y Video /// '
             'Audio para TV"]',
             'StereoSystem'),
            ('["categories.level2:Categorías /// TV y Video /// '
             'DVD y Blu-Ray"]', 'OpticalDiskPlayer'),
            ('["categories.level2:Categorías /// Audio /// '
             'Micro y Minicomponentes"]', 'StereoSystem'),
            ('["categories.level2:Categorías /// Celulares y Tablets /// '
             'Smartphones y Celulares"]', 'Cell'),
            ('["categories.level2:Categorías /// Hogar /// Refrigeración"]',
             'Refrigerator'),
            ('["categories.level2:Categorías /// Electrodomésticos /// '
             'Microondas"]', 'Oven'),
            ('["categories.level3:Categorías /// Cómputo /// '
             'Monitores y Proyectores /// Monitores"]', 'Monitor'),
            ('["categories.level3:Categorías /// Cómputo /// '
             'Monitores y Proyectores /// Proyectores"]', 'Projector'),
            ('["categories.level3:Categorías /// Hogar /// Climatización /// '
             'Aires acondicionados split"]', 'AirConditioner'),
        ]

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        product_urls = []

        for category_filter, local_category in category_filters:
            if local_category != category:
                continue

            page = 0

            while True:
                payload_params = "page={}&facetFilters={}&numericFilters=%5B" \
                                 "%22visibility_catalog%3D1%22%5D" \
                                 "".format(page, urllib.parse.quote(
                                    category_filter))

                payload = {
                    "requests": [{
                        "indexName": "magento2_panafoto_spanish_products",
                        "params": payload_params}]}

                response = session.post(endpoint, data=json.dumps(payload))
                products_json = json.loads(response.text)['results'][0]['hits']

                if not products_json:
                    if page == 0:
                        raise Exception('Empty category: ' + category_filter)
                    break

                for product_json in products_json:
                    product_urls.append(product_json['url'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('form', {'id': 'product_addtocart_form'})[
            'data-product-sku']

        part_number_match = re.search(
            r"ccs_cc_args.push\(\['pn', '(.+)'\]\);", data)
        part_number = part_number_match.groups()[0]

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
