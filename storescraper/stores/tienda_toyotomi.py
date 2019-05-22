import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class TiendaToyotomi(Store):
    @classmethod
    def categories(cls):
        return [
            'AirConditioner',
            'Oven',
            'VacuumCleaner',
            'SpaceHeater',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['6', 'AirConditioner'],
            # ['24_27', 'Oven'],
            ['24_30', 'Oven'],
            ['24_31', 'VacuumCleaner'],
            ['20_2', 'SpaceHeater'],
            ['20_1', 'SpaceHeater'],
            ['20_23', 'SpaceHeater'],
            ['20_21', 'SpaceHeater'],
            ['20_46', 'SpaceHeater'],
            ['20_3', 'SpaceHeater'],
            ['20_44', 'SpaceHeater'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://tienda.toyotomi.cl/index.php?cPath=' + \
                           category_path
            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            raw_links = soup.findAll('li', 'wrapper_prods')

            if not raw_links:
                raise Exception('Empty category: ' + category_url)

            for raw_link in raw_links:
                original_product_url = raw_link.find('a')['href'].split(
                    '&osCsid')[0]
                query_string = urllib.parse.urlparse(
                    original_product_url).query
                product_id = urllib.parse.parse_qs(query_string)[
                    'products_id'][0]
                product_url = 'http://tienda.toyotomi.cl/product_info.php?' \
                              'products_id=' + product_id
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h2').contents[0].strip()

        query_string = urllib.parse.urlparse(url).query
        sku = urllib.parse.parse_qs(query_string)['products_id'][0]

        price = Decimal(remove_words(soup.find('h2', 'price').find(
            'span').text))

        description = html_to_markdown(str(soup.find('div', 'desc_padd')))

        picture_urls = [tag['href'].split('?')[0].replace(' ', '%20') for
                        tag in soup.findAll('a', {'rel': 'fancybox'})]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
