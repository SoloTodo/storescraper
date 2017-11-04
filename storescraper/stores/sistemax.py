import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Sistemax(Store):
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
            'Mouse'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['84', 'VideoCard'],  # Tarjetas de video
            ['59', 'Processor'],  # Procesadores
            ['103', 'Monitor'],  # Monitores LCD
            ['66', 'Motherboard'],  # MB
            ['73_74', 'Ram'],  # RAM
            ['73_77', 'Ram'],  # RAM
            ['79_80', 'StorageDrive'],  # HDD desktop
            ['79_81', 'StorageDrive'],  # HDD notebook
            ['79_83', 'SolidStateDrive'],  # SSD
            ['87', 'PowerSupply'],  # Fuentes de poder
            ['88', 'ComputerCase'],  # Gabinetes c/fuente
            ['95', 'CpuCooler'],  # Coolers CPU
            ['93', 'Mouse'],  # Mouse
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url_webpage = 'http://www.sistemax.cl/webstore/index.php?' \
                          'route=product/category&limit=1000&path=' + \
                          category_path

            product_urls += cls._search_all_urls_and_types(
                url_webpage, session)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h2').text.strip()
        sku = soup.find('input', {'name': 'product_id'})['value'].strip()
        pricing_cells = soup.findAll('td', 'description-right')
        stock_text = pricing_cells[len(pricing_cells) - 1]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        picture_urls = [tag['href'].replace(' ', '%20') for tag in
                        soup.findAll('a', 'cloud-zoom')]

        if stock_text.text.strip() == 'En Stock':
            stock = -1
        else:
            stock = 0

        offer_price_container = soup.find('h3', 'special-price')

        if offer_price_container:
            offer_price = offer_price_container.text.split('$')[1]
            offer_price = Decimal(remove_words(offer_price))

            normal_price = offer_price_container.parent.previous.previous
            normal_price = Decimal(remove_words(normal_price.split('$')[1]))
            if normal_price < offer_price:
                normal_price = offer_price
        else:
            normal_price = Decimal(remove_words(soup.find(
                'h3', 'product-price').text))
            offer_price = normal_price

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

    @classmethod
    def _search_all_urls_and_types(cls, url, session):
        product_urls = []

        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        sub_path = soup.find('div', 'category_list')
        if sub_path:
            for sub_url in sub_path.findAll('a'):
                product_urls += \
                    cls._search_all_urls_and_types(sub_url['href'], session)
        else:
            link_containers = soup.findAll('div', 'product-list')

            for link_container in link_containers:
                original_product_url = link_container.find('a')['href']
                query_string = urllib.parse.urlparse(
                    original_product_url).query
                product_id = urllib.parse.parse_qs(query_string)[
                    'product_id'][0]
                product_url = 'http://www.sistemax.cl/webstore/' \
                              'index.php?route=product/product&product_id=' + \
                              product_id
                product_urls.append(product_url)

        return product_urls
