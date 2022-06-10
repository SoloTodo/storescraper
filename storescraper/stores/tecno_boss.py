from decimal import Decimal
import logging
from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MONITOR, MOUSE, POWER_SUPPLY, \
    RAM, SOLID_STATE_DRIVE, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class TecnoBoss(Store):

    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            RAM,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            MOUSE,
            POWER_SUPPLY,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['memorias-ram', RAM],
            ['ssd', SOLID_STATE_DRIVE],
            ['tarjetas-de-video', VIDEO_CARD],
            ['mouse-y-teclados', MOUSE],
            ['todos-los-productos-1/fuente-de-poder', POWER_SUPPLY],
            ['home-office', MONITOR],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.tecnoboss.cl/{}' \
                              '?page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'main-category-image')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a', 'product-image')['href']
                    product_urls.append(
                        'https://www.tecnoboss.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('form', {'name': 'buy'})['action'].split('/')[-1]

        name = soup.find('meta', {'property': 'og:title'})['content']
        description = soup.find(
            'meta', {'property': 'og:description'})['content']

        price = Decimal(remove_words(soup.find('span', 'form-price').text))
        sku_span = soup.find('span', 'sku_elem')
        if sku_span and sku_span.text != "":
            sku = sku_span.text
        else:
            sku = None

        stock_span = soup.find('span', 'product-form-stock')
        if stock_span:
            stock = int(stock_span.text)
        else:
            stock = 0

        picture_urls = []
        picture_container = soup.find('div', 'carousel-inner')
        if picture_container:
            for image in picture_container.findAll('img'):
                picture_urls.append(image['src'])
        else:
            image = soup.find('div', 'main-product-image').find('img')
            picture_urls.append(image['src'])

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
            description=description
        )

        return [p]
