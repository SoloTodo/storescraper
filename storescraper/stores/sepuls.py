import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, KEYBOARD, HEADPHONES, \
    MONITOR, MOUSE, COMPUTER_CASE, MOTHERBOARD, POWER_SUPPLY, CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Sepuls(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            GAMING_CHAIR,
            KEYBOARD,
            HEADPHONES,
            MONITOR,
            MOUSE,
            COMPUTER_CASE,
            MOTHERBOARD,
            CPU_COOLER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['fuentes-de-poder', POWER_SUPPLY],
            ['sillas', GAMING_CHAIR],
            ['teclados', KEYBOARD],
            ['audifono', HEADPHONES],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['gabinete', COMPUTER_CASE],
            ['placa-madre', MOTHERBOARD],
            ['refrigeracion', CPU_COOLER]
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
                url_webpage = 'https://www.sepuls.cl/{}/?product-page={}' \
                    .format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
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
        response = session.get(url, allow_redirects=False)

        if response.status_code == 301:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if not soup.find('p', 'price') or soup.find('p', 'price').text == '':
            return []
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        if soup.find('p', 'stock').text == 'SIN STOCK':
            stock = 0
        else:
            stock = int(soup.find('p', 'stock').text.split()[0])

        picture_urls = [tag['src'] for tag in soup.find('div', 'woocommerce'
                                                               '-product'
                                                               '-gallery'
                                                               '').findAll(
            'img')]
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
