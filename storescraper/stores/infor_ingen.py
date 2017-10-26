import re

from bs4 import BeautifulSoup
from decimal import Decimal

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
            'CpuCooler',
            'Television',
            'Mouse',
            'Notebook',
            'Printer'
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
            ['92_95', 'CpuCooler'],  # Coolers CPU Aire
            ['92_96', 'CpuCooler'],  # Coolers CPU Liquido
            ['98', 'Monitor'],  # Monitores LCD
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.infor-ingen.com/tienda/index.php?' \
                          'route=product/category&limit=100&path=' + \
                          category_path

            soup = BeautifulSoup(session.get(url_webpage).text, 'html.parser')

            link_containers = soup.findAll('div', 'product-layout')

            for link_container in link_containers:
                original_product_url = link_container.find('a')['href']
                product_id = re.search(r'product_id=(\d+)',
                                       original_product_url).groups()[0]
                product_url = 'https://www.infor-ingen.com/tienda/index.php?' \
                              'route=product/product&product_id=' + product_id
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        pricing_container = soup.find('div', {'id': 'product'}).parent
        name = pricing_container.find('h1').text.strip()
        sku = soup.find('input', {'name': 'product_id'})['value']

        stock = int(soup.find('b', text='STOCK TIENDA:').next.next)

        price_containers = pricing_container.find(
            'img', {'align': 'absmiddle'}).parent.findAll('h2')

        normal_price = Decimal(remove_words(price_containers[0].string))
        offer_price = Decimal(remove_words(price_containers[1].string))

        if offer_price > normal_price:
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
