import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import RAM, VIDEO_CARD, SOLID_STATE_DRIVE, \
    PROCESSOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class SamuraiStore(Store):
    @classmethod
    def categories(cls):
        return [
            RAM,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            PROCESSOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['procesador', PROCESSOR],
            ['ram', RAM],
            ['tarjetas-de-video', VIDEO_CARD],
            ['unidades-de-almacenamiento', SOLID_STATE_DRIVE],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 50:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.samuraistorejp.cl/' \
                              'product-category/{}/page/{}/'.format(
                                url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-small')
                if not product_containers or soup.find('section', 'error-404'):
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

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name_tag = soup.find('h1', 'product-title')

        if not name_tag:
            return []

        name = name_tag.text.strip()

        if 'RIFA' in name:
            return []

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        sku_tag = soup.find('span', 'sku')

        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None

        if 'preventa' in name.lower():
            stock = 0
        elif soup.find('p', 'stock out-of-stock'):
            stock = 0
        elif soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = -1
        price_container = soup.find('p', 'product-page-price').findAll(
            'span', 'woocommerce-Price-amount')[-1]
        offer_price = Decimal(remove_words(price_container.text))
        normal_price = (offer_price * Decimal('1.04')).quantize(0)

        picture_urls = [tag.find('a')['href'] for tag in soup.find('div',
                        'product-gallery').findAll(
                        'div',
                        'woocommerce-product-gallery__image')]
        picture_urls = list(filter(None, picture_urls))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls
        )
        return [p]
