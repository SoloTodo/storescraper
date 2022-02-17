import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


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
            CPU_COOLER,
            'Television',
            'Mouse',
            'Notebook',
            'Printer',
            'Keyboard',
            'KeyboardMouseCombo',
            'ExternalStorageDrive',
            'Headphones',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['60', 'Processor'],  # Procesadores
            ['61', 'Motherboard'],  # MB
            ['73', 'Ram'],  # RAM
            ['75_102', 'StorageDrive'],  # HDD Notebook
            ['75_76', 'StorageDrive'],  # HDD Desktop
            ['75_77', 'SolidStateDrive'],  # SSD
            ['78', 'VideoCard'],  # Tarjetas de video
            ['81_84', 'ComputerCase'],  # Gabinetes c/fuente
            ['81_85', 'ComputerCase'],  # Gabinetes s/fuente
            ['81_82', 'PowerSupply'],  # Fuentes de poder Genericas
            ['81_83', 'PowerSupply'],  # Fuentes de poder Reales
            ['92_95', CPU_COOLER],  # Coolers CPU Aire
            ['92_96', CPU_COOLER],  # Coolers CPU Liquido
            ['98', 'Monitor'],  # Monitores LCD
            ['105_106', 'Mouse'],  # Teclados y mouse
            ['105_123', 'Notebook'],  # Notebooks
            ['75_103', 'ExternalStorageDrive'],  # Discos duros externos
            ['90_91', 'Headphones'],  # Audífonos
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 5:
                    raise Exception('Page overflow: ' + category_path)

                url_webpage = 'https://www.infor-ingen.com/tienda/index.php?' \
                              'route=product/category&limit=100&path={}' \
                              '&page={}'.format(category_path, page)

                print(url_webpage)

                soup = BeautifulSoup(session.get(url_webpage).text,
                                     'html.parser')

                link_containers = soup.findAll('div', 'product-layout')

                if not link_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + category_path)
                    break

                for link_container in link_containers:
                    original_product_url = link_container.find('a')['href']
                    product_id = re.search(r'product_id=(\d+)',
                                           original_product_url).groups()[0]
                    product_url = 'https://www.infor-ingen.com/tienda/' \
                                  'index.php?route=product/product&' \
                                  'product_id=' + product_id
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        pricing_container = soup.find('div', {'id': 'product'}).parent
        name = pricing_container.find('h1').text.strip()
        sku = soup.find('input', {'name': 'product_id'})['value']

        stock = int(soup.find('b', text='STOCK WEB:').next.next) + \
            int(soup.find('b', text='STOCK TIENDA:').next.next)

        offer_price_image_tag = pricing_container.find(
            'img', {'align': 'absmiddle'})

        if offer_price_image_tag:
            price_containers = offer_price_image_tag.parent.findAll('h2')
            normal_price = Decimal(remove_words(price_containers[1].text))
            offer_price = Decimal(remove_words(price_containers[2].text))

            if offer_price > normal_price:
                offer_price = normal_price
        else:
            normal_price = Decimal(soup.find(
                'meta', {'property': 'product:price:amount'})['content'])
            offer_price = normal_price

        description = html_to_markdown(str(soup.find(
            'div', {'id': 'tab-description'})))

        picture_urls = [tag['href'].replace(' ', '%20')
                        for tag in soup.findAll('a', 'thumbnail')
                        if tag['href']]

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
