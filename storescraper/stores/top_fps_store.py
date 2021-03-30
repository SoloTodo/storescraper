import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, STORAGE_DRIVE, POWER_SUPPLY, \
    CPU_COOLER, COMPUTER_CASE, MOUSE, USB_FLASH_DRIVE, MOTHERBOARD, \
    PROCESSOR, RAM, SOLID_STATE_DRIVE, MEMORY_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class TopFpsStore(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            CPU_COOLER,
            COMPUTER_CASE,
            MOUSE,
            USB_FLASH_DRIVE,
            MOTHERBOARD,
            PROCESSOR,
            RAM,
            SOLID_STATE_DRIVE,
            MEMORY_CARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['discos-duros', STORAGE_DRIVE],
            ['fuentes', POWER_SUPPLY],
            ['disipadores', CPU_COOLER],
            ['gabinetes', COMPUTER_CASE],
            ['mouse', MOUSE],
            ['pendrives', USB_FLASH_DRIVE],
            ['placas-madres', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['ram', RAM],
            ['ssd', SOLID_STATE_DRIVE],
            ['tarjetas-sd', MEMORY_CARD],
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
                url_webpage = 'https://topfpsstore.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'shop-container')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('div',
                                                            'product-small'):
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
        name = soup.find('h1', 'product-title').text.strip()
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        normal_price = Decimal(
            remove_words(soup.find('table').findAll('bdi')[1].text))
        offer_price = Decimal(
            remove_words(soup.find('table').findAll('bdi')[0].text))
        picture_containers = soup.find('div', 'product-gallery'). \
            findAll('div', 'woocommerce-product-gallery__image')
        picture_urls = [tag.find('img')['src'] for tag in picture_containers]
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
            picture_urls=picture_urls
        )
        return [p]
