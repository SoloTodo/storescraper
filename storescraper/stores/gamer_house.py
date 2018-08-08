import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class GamerHouse(Store):
    @classmethod
    def categories(cls):
        return [
            'VideoGameConsole',
            'Headphones',
            'Keyboard',
            'Mouse',
            'VideoCard',
            'CpuCooler',
            'KeyboardMouseCombo',
            'StorageDrive',
            'SolidStateDrive',
            'Ram',
            'Motherboard',
            'ComputerCase',
            'UsbFlashDrive',
            'PowerSupply',
            'Processor',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_info = [
            ['16', 'VideoGameConsole'],  # Consolas Sony
            ['33', 'VideoGameConsole'],  # Consolas Microsoft
            ['31', 'VideoGameConsole'],  # Consolas Nintendo
            ['51', 'Headphones'],  # Auriculares
            ['24', 'Headphones'],  # Auriculares
            ['21', 'Keyboard'],  # Teclados
            ['22', 'Mouse'],  # Mouse
            ['35', 'VideoCard'],  # Tarjetas Graficas
            ['36', 'CpuCooler'],  # Refrigeración
            ['37', 'KeyboardMouseCombo'],  # Mouse y Teclado
            ['47', 'KeyboardMouseCombo'],  # KITS GAMER
            ['38', 'StorageDrive'],  # Almacenamiento
            ['39', 'Ram'],  # Memorias Ram
            ['40', 'Motherboard'],  # Placas Madres
            ['44', 'ComputerCase'],  # Gabinetes
            ['46', 'UsbFlashDrive'],  # Pendrives
            ['48', 'PowerSupply'],  # Fuentes de Poder
            ['49', 'Processor'],  # Procesadores
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_id, local_category in category_info:
            if local_category != category:
                continue

            category_url = 'https://www.gamerhouse.cl/modules/blocklayered/' \
                           'blocklayered-ajax.php?id_category_layered={}' \
                           '&n=1000'.format(category_id)
            json_data = json.loads(session.get(category_url).text)
            soup = BeautifulSoup(json_data['productList'], 'html.parser')

            containers = soup.findAll('li', 'ajax_block_product')

            if not containers:
                raise Exception('Empty category: ' + category_id)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value']

        availability = soup.find('link', {'itemprop': 'availability'})

        if availability and availability['href'] == \
                'https://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('span', {'itemprop': 'price'})['content'])
        description = html_to_markdown(
            str(soup.find('section', 'page-product-box')))

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'fancybox')]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
