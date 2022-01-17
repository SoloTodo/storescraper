import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, VIDEO_CARD, NOTEBOOK, PROCESSOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Meritek(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            VIDEO_CARD,
            NOTEBOOK,
            PROCESSOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gaming/accesorios', HEADPHONES],
            ['hardware-tecno/perifericos', HEADPHONES],
            ['hardware-tecno/procesadores', PROCESSOR],
            ['hardware-tecno/tarjetadevideo', VIDEO_CARD],
            ['tecnologia/notebooks', NOTEBOOK],
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

                url_webpage = 'https://meritek.cl/categoria-producto/{}/page' \
                              '/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                if not soup.find('ul', 'products'):
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break
                product_containers = BeautifulSoup(
                    json.loads(
                        soup.find('ul', 'products').find('script').text),
                    'html.parser').findAll('li', 'product-col')

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
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        soup = BeautifulSoup(
            json.loads(soup.find('div', 'product').find('script').text),
            'html.parser')
        sku_tag = soup.find('span', 'sku')
        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None
        name = soup.find('h2', 'product_title').text.strip()
        if soup.find('span', 'product-stock in-stock'):
            stock = int(
                soup.find('span', 'product-stock in-stock').text.split(' ')[1])
        else:
            stock = 0
        if soup.find('p', 'price').find('ins'):
            price = Decimal(remove_words(soup.find('p', 'price').find('ins'
                                                                      ).text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').find('bdi'
                                                                      ).text))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'product-images').findAll('img')]
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
            sku=sku,
            picture_urls=picture_urls,
            part_number=sku
        )
        return [p]
