import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Spider(Store):
    @classmethod
    def categories(cls):
        return [
            'VideoCard',
            'Processor',
            'Monitor',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'ExternalStorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'CpuCooler',
            'Mouse',
            'Notebook',
            'Tablet',
            'Printer',
            'Keyboard',
            'KeyboardMouseCombo',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ('41', 'Notebook'),
            # ('43', 'Notebook'),   # Ultrabooks
            ('26', 'StorageDrive'),
            ('44', 'SolidStateDrive'),
            ('29', 'Motherboard'),
            ('31', 'ComputerCase'),
            ('36', 'Ram'),
            ('235', 'ExternalStorageDrive'),
            ('28', 'Processor'),
            ('30', 'VideoCard'),
            ('32', 'PowerSupply'),
            ('34', 'CpuCooler'),
            ('21', 'Monitor'),
            ('25', 'Tablet'),
            ('49', 'Printer'),
            ('50', 'Printer'),
            ('48', 'Printer'),
            ('55', 'Mouse'),
            ('56', 'Keyboard'),
            ('57', 'KeyboardMouseCombo'),
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.spider.cl/modules/blocklayered/' \
                          'blocklayered-ajax.php?id_category_layered={}' \
                          '&n=1000'.format(category_path)

            json_data = json.loads(session.get(url_webpage).text)
            soup = BeautifulSoup(json_data['productList'], 'html.parser')

            product_containers = soup.findAll('li', 'ajax_block_product')

            if not product_containers:
                raise Exception('Empty category: ' + category_path)

            for product_container in product_containers:
                product_url = product_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('input', {'id': 'product_page_product_id'})['value']

        if soup.find('link', {'itemprop': 'availability'}):
            stock = -1
        else:
            stock = 0

        price_containers = soup.findAll('span', {'id': 'our_price_display'})

        offer_price = Decimal(price_containers[0]['content'])
        normal_price = Decimal(remove_words(price_containers[1].text))

        part_number = soup.find('span', {'itemprop': 'sku'}).text.strip()

        description = html_to_markdown(str(soup.find(
            'section', 'page-product-box')))

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'fancybox')]

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
