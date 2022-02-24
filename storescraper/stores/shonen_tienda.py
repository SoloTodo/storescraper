import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PROCESSOR, VIDEO_CARD, RAM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class ShonenTienda(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            VIDEO_CARD,
            RAM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['all', PROCESSOR],
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
                url_webpage = 'https://shonen.cl/collections/{}?page={}'. \
                    format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'grid__item')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://shonen.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        description = html_to_markdown(
            str(soup.find('div', 'product-single__description')))

        if 'SOLO CPU' in description.upper():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        name = soup.find('h1', 'product-single__title').text
        sku = soup.find('form', 'product-form')['id'].split('_')[-1]

        if len(soup.find('span', 'variant-sku').text.split()) > 1:
            part_number = soup.find('span', 'variant-sku').text.split()[1]
        else:
            part_number = None

        if soup.find('div', {'id': 'variant-inventory'}):
            stock = int(soup.find('div', {
                'id': 'variant-inventory'}).text.strip().split()[1])
        else:
            stock = 0

        price = Decimal(
            remove_words(soup.find('span', 'price-item').text.strip()))
        if soup.find('ul', 'product-single__thumbnails'):
            picture_urls = ['https:' + tag['src'].split('?v')[0] for tag in
                            soup.find('ul', 'product-single__thumbnails')
                                .findAll('img')]
        else:
            picture_urls = ['https:' + soup.find('img', {
                'id': 'FeaturedMedia-product-template'})['src'].split('?v')[0]]
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
            condition=condition,
            description=description
        )
        return [p]
