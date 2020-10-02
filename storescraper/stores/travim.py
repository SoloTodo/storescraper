from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Travim(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            'VideoCard',
            'ComputerCase',
            'Mouse',
            'Keyboard',
            'Monitor',
            'Tablet',
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['disco-duro-interno', 'StorageDrive'],
            ['ssd', 'SolidStateDrive'],
            ['mother-board', 'Motherboard'],
            ['procesador-intel', 'Processor'],
            ['procesador-amd', 'Processor'],
            ['t-video', 'VideoCard'],
            ['gabinete', 'ComputerCase'],
            ['mouse', 'Mouse'],
            ['teclado', 'Keyboard'],
            # ['monitores', 'Monitor'],
            ['tablet', 'Table'],
            ['smartphones', 'Cell']
        ]

        base_url = 'https://travim.com.mx/categoria-producto/{}/page/{}/'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)
                print(url)

                if page >= 15:
                    raise Exception('Page overflow: ' + url)

                response = session.get(url)

                if response.status_code == 404:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                product_container = soup.find('ul', 'products')
                products = product_container.findAll('li', 'product')

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('span', 'sku').text

        stock = soup.find('p', 'in-stock')

        price = soup.find('span', 'woocommerce-Price-amount')\
            .text.replace('MXN', '').replace(',', '').strip()
        price = Decimal(price)

        if not stock:
            stock = 0
        else:
            stock = int(stock.text.split()[0])

        picture_urls = [x['src'] for x in
                        soup.findAll('img', 'attachment-300x300')]

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
        )

        return [p]
