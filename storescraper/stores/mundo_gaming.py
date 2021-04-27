import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class MundoGaming(Store):
    @classmethod
    def categories(cls):
        return [
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['sillas-gamer', GAMING_CHAIR]
        ]
        session = session_with_proxy(extra_args)
        session.headers['x-requested-with'] = 'XMLHttpRequest'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.mundogaming.cl/categoria/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.post(url_webpage, data='portoajax=true').text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('li',
                                                            'product-col'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['x-requested-with'] = 'XMLHttpRequest'
        response = session.post(url, data='portoajax=true')
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h2', 'product_title').text.strip()
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        stock = int(soup.find('span', 'stock').text.split()[0])
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        picture_urls = [tag['src'].replace('-150x150', '') for tag in
                        soup.find('div', 'product-thumbnails').findAll('img')]
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
