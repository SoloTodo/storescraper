from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Cintegral(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Tablet',
            'StorageDrive',
            'PowerSupply',
            'ComputerCase',
            'Ram',
            'Monitor',
            'Processor',
            'VideoCard',
            'Motherboard',
            'Printer',
            'Cell',
            'Mouse',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'http://www.cintegral.cl/'

        category_paths = [
            ['9', 'Notebook'],
            ['89', 'Tablet'],
            ['98', 'Cell'],
            ['18', 'Processor'],
            ['2', 'StorageDrive'],
            ['59', 'StorageDrive'],
            ['7', 'ComputerCase'],
            ['54', 'PowerSupply'],
            ['19', 'Motherboard'],
            ['4', 'Ram'],
            ['49', 'Ram'],
            ['14', 'VideoCard'],
            ['31', 'Printer'],
            ['32', 'Printer'],
            ['34', 'Printer'],
            ['1', 'Monitor'],
            ['17', 'Mouse'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            page = 1

            while True:
                category_url = '{}categoria.php?categoria={}&pagina={}'.format(
                    base_url, category_path, page)
                print(category_url)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                base_soup = BeautifulSoup(session.get(category_url).text,
                                          'html.parser')

                product_containers = \
                    base_soup.findAll('div', 'casilla-producto')

                if not product_containers and page == 1:
                    raise Exception('Empty category: ' + category_url)

                product_found = False

                for container in product_containers:
                    link = container.find('a')
                    if not link:
                        continue

                    product_found = True

                    product_url = base_url + link['href'].replace(' ', '%20')
                    product_urls.append(product_url)

                if not product_found:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'nombre-producto-catalogo')\
            .find('span').string.strip()

        sku = soup.find('input', {'name': 'idprod'})['value']

        stock_containers = soup.findAll('td', 'columna-derecha-tabla-catalogo')

        if not stock_containers:
            stock = 0
        else:
            stock = int(stock_containers[-1].find('span').text)

        normal_price = Decimal(remove_words(
            soup.find('div', 'precio-producto-catalogo').find('span').string))
        offer_price = normal_price

        description = html_to_markdown(
            str(soup.find('div', {'id': 'ficha-producto'})))

        picture_urls = ['http://www.cintegral.cl/' +
                        soup.find('a', 'highslide')['href'].replace(
                            ' ', '%20')]

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
