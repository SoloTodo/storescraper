from bs4 import BeautifulSoup

from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Huawei(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Cell',
            'Tablet',
            'Wereable'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Notebooks
            ['403', 'Notebook'],
            # Cells
            ['387', 'Cell'],
            # Tablets
            ['407', 'Tablet'],
            # Wereables
            ['399', 'Wereable'],
            # Headphones
            ['391', 'Headphone']
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            offset = 1
            while True:
                url_webpage = 'https://shop.huawei.com/cl/list-data-{}?sortField=registterTime&' \
                              'sortType=desc&prdAttrList=%5B%5D&pageNumber={}&pageSize=9'.format(url_extension, offset)

                data = session.get(url_webpage).text

                soup = BeautifulSoup(data, 'html5lib')
                product_container = soup.findAll('li', 'dataitem')

                if not product_container:
                    break
                for container in product_container:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                offset += 1

        return product_urls


