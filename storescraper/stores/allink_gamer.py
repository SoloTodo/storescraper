import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import COMPUTER_CASE, KEYBOARD, MOUSE, \
    HEADPHONES, GAMING_CHAIR, MONITOR, KEYBOARD_MOUSE_COMBO, POWER_SUPPLY, \
    CPU_COOLER, STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class AllinkGamer(Store):
    @classmethod
    def categories(cls):
        return [
            COMPUTER_CASE,
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            GAMING_CHAIR,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            POWER_SUPPLY,
            CPU_COOLER,
            STEREO_SYSTEM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['26-gabinetes', COMPUTER_CASE],
            ['27-teclados', KEYBOARD],
            ['19-mouse', MOUSE],
            ['39-audifonos', HEADPHONES],
            ['18-sillas', GAMING_CHAIR],
            ['35-monitores', MONITOR],
            ['38-kits-gamer', KEYBOARD_MOUSE_COMBO],
            ['41-fuentes-de-poder', POWER_SUPPLY],
            ['43-parlantes', STEREO_SYSTEM],
            ['44-refrigeracion-liquida', CPU_COOLER]
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

                url_webpage = 'https://allinkgamer.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('section', {'id': 'products'}) \
                    .findAll('article')
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
        stock = int(
            soup.find('div', 'more-infor-product product-quantities').find(
                'span')['data-stock'])
        price = Decimal(soup.find('span', {'itemprop': 'price'})['content'])
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'images-container').findAll('img')]
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
