import re
import urllib

import requests
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown


class InforIngen(Store):
    @classmethod
    def categories(cls):
        return [
            'VideoCard',
            'Processor',
            'Monitor',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'CpuCooler',
            'Television',
            'Mouse',
            'Notebook',
            'Printer'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['156', 'Notebook'],
            ['59', 'Processor'],  # Procesadores
            ['66', 'Motherboard'],  # MB
            ['72_73', 'StorageDrive'],  # HDD Desktop
            ['72_74', 'StorageDrive'],  # HDD Notebook
            ['72_135', 'SolidStateDrive'],  # SSD
            ['98_101', 'ComputerCase'],  # Gabinetes c/fuente
            ['98_102', 'ComputerCase'],  # Gabinetes s/fuente
            ['98_99', 'PowerSupply'],  # Fuentes de poder Genéricas
            ['98_100', 'PowerSupply'],  # Fuentes de poder Reales
            ['103', 'Printer'],  # Impresoras
            ['108', 'Ram'],  # RAM
            ['112_113', 'Monitor'],  # Monitores LCD
            ['112_114', 'Television'],  # Televisores
            ['115_119', 'Mouse'],  # Mouse PC
            ['146', 'CpuCooler'],  # Coolers CPU
            ['127', 'VideoCard'],  # Tarjetas de video
        ]

        product_urls = []
        session = requests.Session()

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'http://www.infor-ingen.com/index.php?' \
                          'route=product/category&limit=1000&path=' + \
                          category_path

            soup = BeautifulSoup(session.get(url_webpage).text, 'html.parser')
            soup = soup.find('div', 'product-list')

            if not soup:
                raise Exception('Empty category: ' + category_path)

            link_containers = soup.findAll('div', 'image')

            for link_container in link_containers:
                original_product_url = link_container.find('a')['href']
                product_id = re.search(r'product_id=(\d+)',
                                       original_product_url).groups()[0]
                product_url = 'http://www.infor-ingen.com/index.php?route=' \
                              'product/product&product_id=' + product_id
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = requests.Session()
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('meta', {'itemprop': 'name'})['content'].strip()
        sku = soup.find('input', {'name': 'product_id'})['value'].strip()

        availability = soup.find('link',
                                 {'itemprop': 'availability'})['href'].strip()
        description = html_to_markdown(str(soup.find(
            'div', {'id': 'tab-description'})))

        if availability == 'http://schema.org/InStock':
            stock_text = soup.find('div', 'description').text
            stock_match = re.search(r'Cantidad: (\d+)', stock_text)
            if stock_match:
                stock = int(stock_match.groups()[0])
            else:
                stock = -1
        else:
            stock = 0

        product_price_container = soup.find('div', 'price-cart')

        normal_price = product_price_container.find('span', 'price-old').text
        normal_price = Decimal(remove_words(normal_price))

        offer_price = product_price_container.find('span', 'price-new').text
        offer_price = Decimal(remove_words(offer_price))

        picture_urls = []
        picture_links = soup.findAll('a', 'colorbox')

        if len(picture_links) > 1:
            picture_links = picture_links[1:]

        for picture_link in picture_links:
            picture_url = picture_link['href'].replace(' ', '%20')
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
            picture_urls=picture_urls
        )

        return [p]
