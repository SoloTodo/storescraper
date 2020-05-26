from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, \
    html_to_markdown


class Dimercom(Store):
    @classmethod
    def categories(cls):
        return [
            # 'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            # 'Ups',
            'Mouse',
            'Keyboard',
            'Monitor',
            'Tablet',
            # 'Printer',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['6_109', 'StorageDrive'],
            ['6_110', 'SolidStateDrive'],
            ['27_255', 'Motherboard'],
            ['27_257', 'Motherboard'],
            # A-Series
            ['17_175', 'Processor'],
            # AMD
            ['7_176', 'Processor'],
            # Celeron
            ['17_177', 'Processor'],
            # Core
            ['17_178', 'Processor'],
            # Pentium
            ['17_181', 'Processor'],
            # Ryzen
            ['17_182', 'Processor'],
            ['13_138', 'Ram'],
            ['13_139', 'Ram'],
            ['26_253', 'VideoCard'],
            ['26_254', 'VideoCard'],
            ['9_116', 'PowerSupply'],
            ['10_123', 'ComputerCase'],
            ['1_64', 'Keyboard'],
            ['1_56', 'Mouse'],
            ['14', 'Monitor'],
            ['25_250', 'Tablet'],
            ['12_131', 'Printer'],
            ['12_132', 'Printer']

        ]

        base_url = 'https://www.dimercom.mx/index.php?' \
                   'route=product/category&path={}&page={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)
                print(url)

                if page > 20:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_container = soup.find('div', 'product-list')

                if not product_container:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                products = product_container.findAll('div', 'image')

                for product in products:
                    if product.find('a'):
                        product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html5lib')

        name = soup.find('div', 'right').find('h1').text
        sku = soup.find('input', {'name': 'product_id'})['value']

        description_data = soup.find('div', 'description').findAll('span')

        stock = 0

        for data in description_data:
            split_data = data.text.split(':')
            if len(split_data) > 1:
                if "Disponible" in split_data[0]:
                    stock = int(split_data[1])

        if not stock:
            if 'Disponible' in soup.find('div', 'description').text:
                stock = -1

        price = Decimal(
            soup.find('span', 'price-fixed').text
                .replace('$', '').replace(',', ''))

        picture_urls = [
            soup.find('a', 'jqzoom colorbox')['href'].replace(' ', '%20')]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

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
            'MXN',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
