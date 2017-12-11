import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Hites(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'HomeTheater',
            'VideoGameConsole',
            'AllInOne',
            'SpaceHeater',
            'CellAccesory',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://www.hites.com/tienda/ProductListingView?' \
                   'categoryId='

        url_extensions = [
            ['14002', 'Refrigerator'],
            ['14067', 'Notebook'],
            ['14114', 'Television'],
            ['14068', 'Tablet'],
            ['14070', 'Printer'],
            ['14022', 'Oven'],
            ['14023', 'Oven'],
            ['14046', 'VacuumCleaner'],
            ['14014', 'WashingMachine'],
            ['14017', 'WashingMachine'],
            ['14015', 'WashingMachine'],
            ['14108', 'Cell'],
            ['14074', 'Camera'],
            ['14082', 'StereoSystem'],
            ['14083', 'StereoSystem'],
            ['14120', 'OpticalDiskPlayer'],
            ['14079', 'HomeTheater'],
            ['14087', 'VideoGameConsole'],
            ['14065', 'AllInOne'],
            # ['14054', 'SpaceHeater'],
            # ['14051', 'SpaceHeater'],
            # ['14052', 'SpaceHeater'],
            # ['14056', 'SpaceHeater'],  # Termoventiladores
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        for category_id, local_category in url_extensions:
            if local_category != category:
                continue

            category_url = url_base + category_id

            soup = BeautifulSoup(session.post(
                category_url,
                'pageSize=1000&storeId=10151').text, 'html.parser')

            divs = soup.findAll('div', 'product')
            category_product_urls = [div.find('a')['href'] for div in divs]

            if not category_product_urls:
                raise Exception('No products found for {}'.format(
                    category_url))

            for product_url in category_product_urls:
                product_url = product_url.replace('http://', 'https://')

                if 'ProductDisplay' in product_url:
                    parsed_product = urllib.parse.urlparse.urlparse(
                        product_url)
                    parameters = urllib.parse.urlparse.parse_qs(
                        parsed_product.query)

                    parameters = {
                        k: v for k, v in parameters.items()
                        if k in ['urlRequestType', 'productId', 'storeId']}

                    newqs = urllib.parse.urlencode(parameters, doseq=True)

                    product_url = \
                        'https://www.hites.com/tienda/ProductDisplay?' + newqs

                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url, timeout=30).text
        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('div', {'id': 'errorPage'}):
            return []

        sku = soup.find('meta', {'name': 'pageIdentifier'})['content']

        description = ''

        for panel in soup.findAll('div', 'descripcion-producto'):
            description += html_to_markdown(str(panel)) + '\n\n'

        if soup.find('div', 'noDisponible_button'):
            stock = 0

            name = soup.find('h1', {'role': 'heading'}).text
            price_str = soup.find(
                'input', {'id': 'hitesprice_paymentTerms'})['value']

            if not price_str:
                return []

            normal_price = Decimal(price_str)
            offer_price = normal_price
        else:
            stock = -1

            catentry_id = re.search(r'"catentry_id" : "(\d+)"',
                                    page_source).groups()[0]

            ajax_url = 'https://www.hites.com/tienda/' \
                       'GetCatalogEntryDetailsByIDView?storeId=10151' \
                       '&catalogEntryId=' + catentry_id

            ajax_body = session.get(ajax_url).text

            json_body = re.search(r'/\*([\S\s]+)\*/', ajax_body).groups()[0]
            json_body = json_body.replace('\n', '').replace('\t', '').replace(
                '\r', '').replace('\x1a', '')
            json_body = json.loads(json_body)['catalogEntry']

            name = json_body['description'][0]['name']

            normal_price = remove_words(json_body['offerPrice'])
            if normal_price == '':
                return []

            normal_price = Decimal(normal_price)

            offer_price = remove_words(json_body['hitesPrice'])
            if offer_price:
                offer_price = Decimal(offer_price)
                if offer_price > normal_price:
                    offer_price = normal_price
            else:
                offer_price = normal_price

        # Pictures

        page_id = soup.find('meta', {'name': 'pageId'})['content']
        gallery_content = soup.find(
            'div', {'id': 'entitledItem_' + page_id}).text
        gallery_content = re.sub(r'"DescriptiveAttributes"[\S\s]*?},', '',
                                 gallery_content)
        gallery_json = json.loads(gallery_content)

        picture_urls = [
            'https://www.hites.com' +
            soup.find('img', {'id': 'productMainImage'})['src']
        ]

        if gallery_json and 'ItemAngleFullImage' in gallery_json[0]:
            sorted_pictures = sorted(
                gallery_json[0]['ItemAngleFullImage'].items(),
                key=lambda pair: int(pair[0].replace('image_', '')))
            for picture_pair in sorted_pictures:
                picture_url = 'https://www.hites.com' + picture_pair[1]
                if picture_url not in picture_urls:
                    picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            cell_plan_name=None,
            cell_monthly_payment=None,
            picture_urls=picture_urls
        )

        return [p]
