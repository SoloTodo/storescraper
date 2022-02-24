import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import KEYBOARD, MOUSE, HEADPHONES, \
    COMPUTER_CASE, CPU_COOLER, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class ElCofreDeShepard(Store):
    @classmethod
    def categories(cls):
        return [
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            COMPUTER_CASE,
            CPU_COOLER,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['teclados-1', KEYBOARD],
            ['mouses', MOUSE],
            ['audifonos', HEADPHONES],
            ['gabinetes', COMPUTER_CASE],
            ['ventiladores', CASE_FAN]
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

                url_webpage = 'https://www.elcofredeshepard.cl/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.elcofredeshepard.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h2').text.strip()
        sku = soup.find('form', 'product-form')['action'].split('/')[-1]
        if soup.find('span', 'product-form-stock'):
            stock = int(soup.find('span', 'product-form-stock').text)
        else:
            stock = 0
        normal_price = Decimal(remove_words(
            soup.findAll('font', {'color': 'ff0000'})[1].text.strip().split()[
                0]))
        offer_price = Decimal(remove_words(
            soup.findAll('font', {'color': 'ff0000'})[0].text.strip().split()[
                0]))
        picture_urls = [
            tag['src'].replace('resize/100/100', 'resize/500/500')
            .split('?')[0]
            for tag in soup.find('div', 'owl-thumbs').findAll('img')
        ]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,

        )
        return [p]
