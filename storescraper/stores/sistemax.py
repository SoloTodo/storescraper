from bs4 import BeautifulSoup

from storescraper.store import Store
from storescraper.utils import session_with_proxy


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
        pass

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
                product_url = link_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls
