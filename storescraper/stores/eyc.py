import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, TABLET, STORAGE_DRIVE, RAM, \
    PROCESSOR, PRINTER, UPS
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Eyc(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            STORAGE_DRIVE,
            RAM,
            PROCESSOR,
            PRINTER,
            UPS
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['294-notebooks', NOTEBOOK],
            ['313-tablets', TABLET],
            ['330-discos', STORAGE_DRIVE],
            ['306-discos', STORAGE_DRIVE],
            ['304-memorias', RAM],
            ['305-procesadores', PROCESSOR],
            ['331-impresoras', PRINTER],
            ['300-ups', UPS]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://tienda.eyc.cl/es/{}?page={}'. \
                    format(url_extension, page)
                data = session.get(url_webpage, verify=False).text
                soup = BeautifulSoup(data, 'html.parser')
                product_container = soup.findAll('article',
                                                 'product-miniature')
                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_container:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('div', 'product-reference_top').find(
            'span').text + ' - ' + soup.find('h1', 'product_name').text
        sku = soup.find('input', {'name': 'id_product'})['value']
        stock = -1
        price = Decimal(soup.find('span', 'price')['content'])
        picture_urls = [tag['src'] for tag in
                        soup.find('ul', 'product-images').findAll('img')]
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
            picture_urls=picture_urls
        )
        return [p]
