import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class PortatilChile(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            NOTEBOOK
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow')
                url_webpage = 'https://portatilchile.com/4-notebooks?page={}' \
                              ''.format(page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('article',
                                                  'product-miniature')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category')
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'h1 page-title').text
        sku = soup.find('input', {'name': 'id_product'})['value'].strip()
        part_number = soup.find('span', {'itemprop': 'sku'}).text.strip()
        stock_container = soup.find('div', 'product-quantities')
        if stock_container:
            stock = int(stock_container.find('span')['data-stock'])
        else:
            stock = 0
        price = Decimal(remove_words(soup.find('span', 'current-price').text))
        if soup.find('div', {'id': 'product-images-thumbs'}):
            picture_urls = [tag['data-image-large-src'] for tag in
                            soup.find('div',
                                      {'id': 'product-images-thumbs'}).findAll(
                                'img')]
        else:
            picture_urls = [
                soup.find('div', 'images-container').find('img')[
                    'data-image-large-src']]

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
            part_number=part_number,
            picture_urls=picture_urls,
        )

        return [p]
