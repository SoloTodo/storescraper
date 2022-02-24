import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
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
            CPU_COOLER,
            'Mouse',
            'Notebook',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'StereoSystem',
            'VideoGameConsole',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['59', 'Processor'],  # Procesadores
            ['84', 'VideoCard'],  # Tarjetas de video
            ['103', 'Monitor'],  # Monitores LCD
            ['66', 'Motherboard'],  # MB
            ['73_74', 'Ram'],  # RAM
            ['73_77', 'Ram'],  # RAM
            ['79_80', 'StorageDrive'],  # HDD desktop
            ['79_81', 'StorageDrive'],  # HDD notebook
            ['79_83', 'SolidStateDrive'],  # SSD
            ['87', 'PowerSupply'],  # Fuentes de poder
            ['88', 'ComputerCase'],  # Gabinetes c/fuente
            ['95', CPU_COOLER],  # Coolers CPU
            ['93', 'Mouse'],  # Mouse
            ['115', 'Notebook'],  # Notebook
            ['92', 'Keyboard'],  # Teclados
            ['99_102', 'Headphones'],  # AUDIFONOS
            ['99_100', 'StereoSystem'],  # PARLANTES
            ['144', 'VideoGameConsole'],  # CONSOLAS
        ]

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url_webpage = 'http://www.sistemax.cl/index.php?' \
                          'route=product/category&limit=1000&path=' + \
                          category_path

            product_urls += cls._search_all_urls_and_types(
                url_webpage, session)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text.strip()
        sku = soup.find(
            'input', {'type': 'hidden', 'name': 'product_id'})['value']

        part_number = soup.find('p', {'id': 'pn'}).text[:49]
        pricing_cells = soup.findAll('h3', 'special-price')
        if len(pricing_cells) > 1:
            normal_price = Decimal(
                pricing_cells[1].text.split('$')[-1].replace(',', ''))
            offer_price = Decimal(
                pricing_cells[2].text.split('$')[-1].replace(',', ''))
        else:
            normal_price = Decimal(
                remove_words(soup.find(
                    'div', {'id': 'product'}).parent.find('h2').text))
            offer_price = normal_price

        if offer_price > normal_price:
            offer_price = normal_price

        stock_container = soup.find('p', {'id': 'stock'})

        if stock_container.text.strip() == 'En Stock':
            stock = -1
        else:
            stock = 0

        description = html_to_markdown(str(soup.find(
            'div', 'tab-content').div))
        picture_container = soup.find('ul', 'thumbnails')

        if picture_container:
            picture_urls = []
            for tag in picture_container.findAll('a'):
                picture_url = tag['href'].replace(' ', '%20')\
                    .replace('\xa0', '%C2%A0')
                if picture_url != '':
                    picture_urls.append(picture_url)
        else:
            picture_urls = None

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
            part_number=part_number,
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

    @classmethod
    def _search_all_urls_and_types(cls, url, session):
        print('Searching ', url)
        product_urls = []

        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        sub_path_links = soup.find('div', {'id': 'content'}).findAll('li')
        if sub_path_links:
            print('Is subpath')
            for sub_path_link in sub_path_links:
                sub_url = sub_path_link.find('a')
                product_urls += \
                    cls._search_all_urls_and_types(sub_url['href'], session)
        else:
            print('Is final')
            link_containers = soup.findAll('div', 'product-list')

            for link_container in link_containers:
                original_product_url = link_container.find('a')['href']
                query_string = urllib.parse.urlparse(
                    original_product_url).query
                product_id = urllib.parse.parse_qs(query_string)[
                    'product_id'][0]
                product_url = 'http://www.sistemax.cl/' \
                              'index.php?route=product/product&product_id=' + \
                              product_id
                product_urls.append(product_url)

        return product_urls
