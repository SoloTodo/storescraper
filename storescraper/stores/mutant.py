from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import CPU_COOLER, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, \
    session_with_proxy


class Mutant(Store):
    @classmethod
    def categories(cls):
        return [
            CPU_COOLER,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['categoria-componentes', CPU_COOLER],
            ['categoria-perifericos', MOUSE],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.mutant.cl/{}/'.format(url_extension)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', 'jet-woo-products__item')

            if not product_containers:
                logging.warning('Empty category: ' + url_extension)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]

        name = soup.find('h1', 'product_title').text.strip()

        price_container = soup.find('p', 'price')
        price = Decimal(remove_words(
            price_container.findAll('span', 'amount')[-1].text))

        stock_container = soup.find('p', 'stock in-stock')
        if stock_container:
            stock = int(stock_container.text.split(' ')[0])
        else:
            stock = 0

        description = html_to_markdown(
            soup.find('div', {'id': 'tab-description'}).text)

        picture_container = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        picture_urls = []
        for a in picture_container.findAll('a'):
            picture_urls.append(a['href'])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            picture_urls=picture_urls,
            description=description
        )
        return [p]
