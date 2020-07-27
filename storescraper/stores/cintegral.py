from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Cintegral(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'AllInOne',
            'Tablet',
            'StorageDrive',
            'ExternalStorageDrive',
            'SolidStateDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'Processor',
            'ComputerCase',
            'PowerSupply',
            'Motherboard',
            'Ram',
            'VideoCard',
            'Mouse',
            'Printer',
            'Headphones',
            'StereoSystem',
            'Ups',
            'Monitor'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://www.cintegral.cl/index.php?' \
                   'id_category={}&controller=category&page={}'

        url_extensions = [
            ['17', 'Notebook'],
            ['84', 'AllInOne'],
            ['85', 'Tablet'],
            ['101', 'StorageDrive'],
            ['102', 'ExternalStorageDrive'],
            ['103', 'SolidStateDrive'],
            ['104', 'MemoryCard'],
            ['105', 'UsbFlashDrive'],
            ['94', 'Processor'],
            ['95', 'ComputerCase'],
            ['96', 'PowerSupply'],
            ['97', 'Motherboard'],
            ['98', 'Ram'],
            ['99', 'VideoCard'],
            ['113', 'Mouse'],
            ['23', 'Printer'],
            ['24', 'Printer'],
            ['25', 'Printer'],
            ['26', 'Printer'],
            ['34', 'Headphones'],
            ['35', 'StereoSystem'],
            ['37', 'Ups'],
            ['15', 'Monitor'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + url_extension)

                url = url_base.format(url_extension, page)
                source = session.get(url, verify=False).text
                soup = BeautifulSoup(source, 'html.parser')

                products = soup.find('div', 'products row')

                if page == 1 and not products:
                    raise Exception('Empty category: ' + url)

                if not products:
                    break

                containers = soup.find('div', 'products row') \
                    .findAll('a', 'product-thumbnail')

                for product_link in containers:
                    product_url = product_link['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url, verify=False).text
        soup = BeautifulSoup(page_source, 'html.parser')
        name = soup.find('h1', 'product-detail-title').text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value']

        part_number = None
        part_number_container = soup.find('span', {'itemprop': 'sku'})
        if part_number_container:
            part_number = part_number_container.text.strip()

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

        if soup.find('i', 'product-available'):
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('div', 'current-price')
                        .find('span', {'itemprop': 'price'})['content'])

        pictures = soup.find('ul', 'product-images').findAll('img')
        picture_urls = [p['data-image-large-src'] for p in pictures]

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
