import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class SionComputer(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'Ram',
            'Monitor',
            'Notebook',
            'Motherboard',
            'Processor',
            'VideoCard',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['80', 'StorageDrive'],    # Disco duro interno
            ['81', 'SolidStateDrive'],    # Discos SSD
            ['82', 'PowerSupply'],    # Fuentes de poder
            ['83', 'ComputerCase'],    # Gabinetes
            ['84', 'Ram'],    # Memoria RAM
            ['104', 'Monitor'],    # Monitores
            ['73', 'Notebook'],    # Notebook
            # ['76', 'Notebook'],    # Ultrabook
            ['85', 'Motherboard'],    # Placas madre
            ['85', 'Motherboard'],    # Placas madre
            ['88', 'Processor'],    # Procesadores AMD
            ['89', 'Processor'],    # Procesadores Intel
            ['89', 'Processor'],    # Procesadores Intel
            ['86', 'VideoCard'],    # Tarjetas de video
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                url = 'https://www.sioncomputer.cl/modules/blocklayered/' \
                      'blocklayered-ajax.php?id_category_layered={}&n=75&' \
                      'p={}'.format(category_path, page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_path)

                json_data = json.loads(session.get(url).text)
                soup = BeautifulSoup(json_data['productList'], 'html.parser')

                containers = soup.findAll('li', 'ajax_block_product')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                for container in containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        sku = soup.find('input', {'name': 'id_product'})['value'].strip()
        part_number = soup.find('span', {'itemprop': 'sku'}).text.strip()
        name = soup.find('h1', {'itemprop': 'name'}).string.strip()

        availability = soup.find('link', {'itemprop': 'availability'})

        if availability['href'] == 'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        normal_price = soup.find('div', 'content_prices').find('span', 'price')
        normal_price = Decimal(remove_words(normal_price.string))

        offer_price = soup.find('span', {'id': 'our_price_display'}).string
        offer_price = Decimal(remove_words(offer_price.string))

        description = html_to_markdown(
            str(soup.find('section', {'id': 'idTab1'})))
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
