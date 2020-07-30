import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class PcGamer(Store):
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
            'Printer',
            'Keyboard',
            'KeyboardMouseCombo',
            'ExternalStorageDrive',
            'Headphones',
            'MemoryCard',
            'UsbFlashDrive',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['62', 'Processor'],  # Procesadores
            ['33', 'Motherboard'],  # MB
            ['70', 'Ram'],  # RAM Notebook
            ['75', 'StorageDrive'],  # Almacenamiento
            ['87', 'VideoCard'],  # Tarjetas de video
            ['81', 'ComputerCase'],  # Gabinetes s/fuente
            ['84', 'PowerSupply'],  # Fuentes de poder
            # ['17_69', 'CpuCooler'],  # Coolers
            ['108', 'CpuCooler'],  # Refrigeracion
            ['106', 'Mouse'],  # Mouse y teclados
            # ['92', 'Keyboard'],  # accesorios gamer
            ['105', 'Headphones'],  # Audio
            ['98', 'Monitor'],  # Monitores
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.54.0'

        product_urls = []

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            subcategory_urls = []

            url_webpage = 'https://www.pc-gamer.cl/index.php?' \
                          'route=product/category&path={}'.format(
                            category_path)

            soup = BeautifulSoup(session.get(url_webpage).text,
                                 'html.parser')

            subcategory_containers = soup.findAll('li', {'data-depth': 1})

            for container in subcategory_containers:
                link = container.find('a')
                if not link:
                    continue
                url = link['href']
                if 'page' in url:
                    continue
                subcategory_urls.append(url)

            if not subcategory_urls:
                subcategory_urls.append(url_webpage)

            for subcategory_url in subcategory_urls:
                page = 1

                while True:
                    if page >= 5:
                        raise Exception('Page overflow: ' + category_path)

                    url_webpage = '{}&page={}'.format(subcategory_url, page)
                    soup = BeautifulSoup(session.get(url_webpage).text,
                                         'html.parser')

                    link_containers = soup.findAll('article', 'item')

                    if not link_containers:
                        break

                    for link_container in link_containers:
                        original_product_url = link_container.find('a')['href']
                        product_id = re.search(
                            r'product_id=(\d+)',
                            original_product_url).groups()[0]
                        product_url = 'https://www.pc-gamer.cl/' \
                                      'index.php?route=product/product&' \
                                      'product_id=' + product_id
                        product_urls.append(product_url)

                    page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.54.0'
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h5', 'ttvproduct-title').text.strip()
        sku = soup.find('input', {'name': 'product_id'})['value']

        stock = int(soup.find(
            'span', 'ttvproduct-stock-status').text.strip())

        price_containers = soup.find('ul', 'product-price-and-shipping')\
            .findAll('h3')
        normal_price = Decimal(remove_words(price_containers[0].text))

        if len(price_containers) > 1:
            offer_price = Decimal(remove_words(price_containers[1].text))
        else:
            offer_price = normal_price

        description = html_to_markdown(str(soup.find(
            'div', {'id': 'tab-description'})))

        picture_urls = [
            soup.find('img', {'id': 'img_zoom'})['data-zoom-image']]

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
