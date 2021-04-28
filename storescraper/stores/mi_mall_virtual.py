import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, KEYBOARD, MOUSE, MONITOR, \
    WEARABLE, POWER_SUPPLY, CPU_COOLER, COMPUTER_CASE, RAM, GAMING_CHAIR, \
    STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MiMallVirtual(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            KEYBOARD,
            MOUSE,
            MONITOR,
            WEARABLE,
            POWER_SUPPLY,
            CPU_COOLER,
            COMPUTER_CASE,
            RAM,
            GAMING_CHAIR,
            STEREO_SYSTEM,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['31-auriculares', HEADPHONES],
            ['20-auriculares-y-audifonos', HEADPHONES],
            ['19-teclados', KEYBOARD],
            ['30-teclados', KEYBOARD],
            ['24-mouse', MOUSE],
            ['29-mouses', MOUSE],
            ['27-monitores', MONITOR],
            ['32-relojes', WEARABLE],
            ['40-fuentes-de-poder-psu', POWER_SUPPLY],
            ['41-fuentes-de-poder-psu', POWER_SUPPLY],
            ['43-enfriador-liquido-cpu', CPU_COOLER],
            ['44-enfriador-liquido-cpu', CPU_COOLER],
            ['36-gabinetes', COMPUTER_CASE],
            ['38-memorias', RAM],
            ['35-sillas', GAMING_CHAIR],
            ['47-parlantes', STEREO_SYSTEM],
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
                url_webpage = 'https://www.mimallvirtual.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('article',
                                                  'product-miniature')
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('input', {'name': 'id_product'})['value']
        if soup.find('button', 'add-to-cart'):
            stock = -1
        else:
            stock = 0
        price = Decimal(soup.find('div', 'product-prices').
                        find('div', 'current-price').
                        find('span')['content'])
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
