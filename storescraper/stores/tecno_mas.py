import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, MONITOR, \
    ALL_IN_ONE, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TecnoMas(Store):
    @classmethod
    def categories(cls):
        return [
            ALL_IN_ONE,
            VIDEO_CARD,
            MONITOR,
            NOTEBOOK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['all-in-one-aio', ALL_IN_ONE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['monitores', MONITOR],
            ['notebooks', NOTEBOOK],
            ['equipos-refaccionados/notebooks-reacondicionados', NOTEBOOK],
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
                url_webpage = 'https://www.tecnomas.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.tecnomas.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'page-title').text.strip()
        key = soup.find('form', 'product-form')['action'].split('/')[-1]
        sku = soup.find('span', 'sku_elem').text.strip()

        if 'CN-' in sku:
            # Manipulated by the store (adding RAM or something), skip
            stock = 0
        else:
            stock_tag = soup.find('span', 'product-form-stock')
            if stock_tag:
                stock = int(stock_tag.text)
            else:
                stock = 0

        if 'REF-' in sku:
            # Refurbished
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        price = Decimal(
            soup.find('meta', {'property': 'product:price:amount'})['content'])

        picture_urls = [tag['src'].split("?")[0] for tag in
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
            part_number=sku,
            picture_urls=picture_urls,
            condition=condition
        )
        return [p]
