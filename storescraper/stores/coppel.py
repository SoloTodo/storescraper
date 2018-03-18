import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Coppel(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_codes = [
            ['13147', 'UsbFlashDrive'],
            ['13341', 'ExternalStorageDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        for category_code, local_category in category_codes:
            if local_category != category:
                continue

            category_url = 'http://www.coppel.com/ProductListingView?' \
                           'storeId=12761&categoryId=' + category_code

            response = session.post(category_url, data='pageSize=1000')
            soup = BeautifulSoup(response.text, 'html.parser')

            containers = soup.findAll('div', 'product')

            if not containers:
                raise Exception('Empty category: ' + category_code)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('div', 'error404'):
            return []

        name = soup.find('h1', 'main_header').text.strip()
        sku = soup.find('input', {'id': 'partNmb'})['value'].strip()

        price = soup.find(
            'span', {'itemprop': 'price'}).contents[0].split('$')[1].replace(
            ',', '')
        price = Decimal(price)

        panel_ids = ['descriptive_attributes', 'long_description']

        description = ''

        for panel_id in panel_ids:
            panel = soup.find('div', {'id': panel_id})
            if panel:
                description += html_to_markdown(str(panel)) + '\n\n'

        pictures_str = re.search(r'"ItemAngleFullImage" : ([\S\s]+?)}',
                                 page_source).groups()[0]
        pictures_json = json.loads(pictures_str + '}')
        picture_urls = list(pictures_json.values())

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'MXN',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
