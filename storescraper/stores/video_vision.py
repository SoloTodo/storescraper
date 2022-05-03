import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR, STORAGE_DRIVE, RAM, UPS, \
    SOLID_STATE_DRIVE, EXTERNAL_STORAGE_DRIVE, MEMORY_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class VideoVision(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            STORAGE_DRIVE,
            RAM,
            UPS,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MEMORY_CARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['monitores-accesorios-cctv', MONITOR],
            ['discos-duros-accesorios', STORAGE_DRIVE],
            ['discos-duros-ssd-internos', SOLID_STATE_DRIVE],
            ['disco-duro-ssd-externo', EXTERNAL_STORAGE_DRIVE],
            ['disco-duro-videovigilancia', STORAGE_DRIVE],
            ['memorias', RAM],
            ['memorias-notebook', RAM],
            ['memorias-pc', RAM],
            ['micro-sd', MEMORY_CARD],
            ['ups', UPS]
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
                url_webpage = 'https://videovision.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'newstore-product')

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
        name = soup.find('h1', 'product_title').text
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        sku = soup.find('span', 'sku').text.strip()
        part_number = soup.find('div',
                                'woocommerce-product-details__short'
                                '-description').text.strip()
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        price = Decimal(remove_words(soup.find('p', 'price').find('bdi').text))
        price = (price * Decimal('1.19')).quantize(0)
        picture_urls = [tag['src'] for tag in soup.find('div',
                                                        'woocommerce-product'
                                                        '-gallery').findAll(
            'img')]
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
            part_number=part_number,
            picture_urls=picture_urls,
        )
        return [p]
