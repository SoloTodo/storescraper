import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class TopPc(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
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
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'StereoSystem',
            'Headphones',
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['24', 'VideoCard'],  # Tarjetas de video
            ['21', 'Processor'],  # Procesadores
            ['78', 'Monitor'],  # Monitores
            ['96', 'Notebook'],  # Notebooks
            ['22', 'Motherboard'],  # MB
            ['23', 'Ram'],  # RAM
            ['44', 'StorageDrive'],  # HDD PC
            ['45', 'StorageDrive'],  # HDD Notebook
            ['46', 'SolidStateDrive'],  # SSD
            ['27', 'PowerSupply'],  # Fuentes de poder
            ['26', 'ComputerCase'],  # Gabinetes
            ['108', CPU_COOLER],  # Coolers CPU
            ['67', 'Mouse'],
            ['66', 'Keyboard'],
            ['65', 'KeyboardMouseCombo'],
            ['100', 'StereoSystem'],
            ['99', 'Headphones'],
            ['109', CASE_FAN],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            category_url = 'http://www.toppc.cl/tienda/{}-'.format(
                category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.findAll('li', 'ajax_block_product')

            if not containers:
                logging.warning('Empty category: ' + category_url)
                break

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value'].strip()

        part_number_container = soup.find('meta', {'name': 'description'})

        if part_number_container:
            part_number = part_number_container['content'].strip()
            if len(part_number) >= 50:
                part_number = None
        else:
            part_number = None

        availability = soup.find('link', {'itemprop': 'availability'})

        if 'VENTA SOLO EN PC ARMADO' in str(soup):
            # Gabinete "VENTA SOLO EN PC ARMADO"
            stock = 0
        elif availability and availability['href'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        offer_price_tag = soup.find('span', {'id': 'our_price_display'})

        if not offer_price_tag:
            return []

        offer_price = offer_price_tag.string
        offer_price = Decimal(remove_words(offer_price))

        normal_price = soup.find(
            'p', {'id': 'old_price'}).find('span', 'price').string
        normal_price = Decimal(remove_words(normal_price))

        description = html_to_markdown(str(soup.find('section',
                                                     'page-product-box')))

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
