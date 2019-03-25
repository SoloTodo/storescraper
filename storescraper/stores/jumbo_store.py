import urllib

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


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
            'Headphones'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('C:/298/302/300/', 'Cell'),
            ('C:/298/303/431/', 'Television'),
            ('C:/298/320/333/', 'Refrigerator'),
            ('C:/298/320/334/', 'WashingMachine'),
            ('C:/298/320/444/', 'Oven'),
            ('C:/298/318/436/', 'Oven'),
            ('C:/298/318/327/', 'VacuumCleaner'),
            ('C:/298/303/312/', 'StereoSystem')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for url_extension, local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + url_extension)

                url = 'https://store.jumbo.cl/buscapagina?fq={}&'\
                      'sl=40921d1c-0864-4f5c-a5d0-ccefd53a1a35&cc=12&'\
                      'sm=0&PS=12&PageNumber={}'\
                    .format(urllib.parse.quote(url_extension, safe=''), page)

                data = session.get(url).text
                soup = BeautifulSoup(data, 'html5lib')

                product_containers = soup.findAll('div', 'box-product')

                import ipdb
                ipdb.set_trace()

                if not product_containers:
                    if page == 0:
                        raise Exception('Empty section: ' + url)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

