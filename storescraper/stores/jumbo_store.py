import re

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    HeadlessChrome


class JumboStore(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Television',
            'Refrigerator',
            'WashingMachine',
            'Oven',
            'VacuumCleaner',
            'StereoSystem',
            'Headphones',
            'Wearable',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('electro-y-tecnologia/electronica/televisores', 'Television'),
            ('electro-y-tecnologia/electrohogar/lavadoras-y-secadoras',
             'WashingMachine'),
            ('electro-y-tecnologia/tecnologia/smartwatch', 'Wearable'),
            # ('electro-y-tecnologia/tecnologia/celulares', 'Cell'),
            # ('electro-y-tecnologia/electrohogar/refrigeradores',
            #  'Refrigerator'),
            # ('electro-y-tecnologia/electrohogar/cocina-y-microondas',
            # 'Oven'),
            # ('electro-y-tecnologia/electrodomesticos/electro-cocina',
            # 'Oven'),
            # ('electro-y-tecnologia/electrodomesticos/aspiradoras',
            #  'VacuumCleaner'),
            # ('electro-y-tecnologia/electronica/parlantes', 'StereoSystem')
        ]

        product_urls = []

        with HeadlessChrome() as driver:
            for url_extension, local_category in category_filters:
                if local_category != category:
                    continue

                url = 'https://store.jumbo.cl/{}?PS=100&sc=20'.format(
                    url_extension)
                print(url)
                driver.get(url)
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                product_containers = soup.findAll('div', 'box-product')

                if not product_containers:
                    raise Exception('Empty section: ' + url)

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url + '?sc=20')

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')
        name = soup.find('div', 'productName').text.strip()
        sku = soup.find('div', 'skuReference').text.strip()
        stock_source = re.search(r'"skuStocks":{"\d+":(\d+)}', page_source)

        if stock_source:
            stock = int(stock_source.groups()[0])
        else:
            print('wat')
            stock = 0

        price_container = soup.find('strong', 'skuBestPrice')
        if not price_container:
            return []
        price = Decimal(price_container.text.replace('$', '').replace(
            '.', '').replace(',', '.'))

        description = html_to_markdown(str(soup.find('div', 'bottom')))
        picture_urls = [tag['zoom'] for tag in
                        soup.findAll('a', {'id': 'botaoZoom'})]

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
