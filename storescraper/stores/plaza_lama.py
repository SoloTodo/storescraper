import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper.categories import TELEVISION, HEADPHONES


class PlazaLama(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only interested in LG products
        url_extensions = [
            ['lg', TELEVISION],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://plazalama.com.do/collections/{}?page={}'.format(
                    url_extension, page)
                print(url)
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-item')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category:' + url)
                    break

                for container in product_containers:
                    product_url = container.find('a', 'product-item__title')[
                        'href']
                    product_urls.append('https://plazalama.com.do' +
                                        product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-meta__title').text
        sku = soup.find('input', {'name': 'id'})['data-sku']
        if soup.find('span', 'product-form__inventory').text == 'Disponible':
            stock = -1
        else:
            stock = 0
        price = Decimal(soup.find('span', 'price').text.strip()
                        .split()[-1].replace(',', ''))
        picture_urls = []
        if soup.find('div', 'product-gallery'):
            picture_urls = ['https:' + tag['data-src'].split('_130')[0] +
                            '.jpg' for tag in
                            soup.find('div', 'product-gallery').find('div',
                            'scroller').findAll('img')]

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
            'DOP',
            sku=sku,
            picture_urls=picture_urls,
        )

        return [p]
