import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, \
    HEADPHONES, GAMING_DESK, POWER_SUPPLY, COMPUTER_CASE, RAM, MONITOR, \
    MOUSE, MOTHERBOARD, PROCESSOR, CPU_COOLER, GAMING_CHAIR, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class FibraNet(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            HEADPHONES,
            GAMING_DESK,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOUSE,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            GAMING_CHAIR,
            VIDEO_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento-externo', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento-interno', STORAGE_DRIVE],
            ['audifonos', HEADPHONES],
            ['escritorios', GAMING_DESK],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['memorias-ram', RAM],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['placas-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['refrigeracion', CPU_COOLER],
            ['sillas', GAMING_CHAIR],
            ['sillas-gamer', GAMING_CHAIR],
            ['tarjetas-de-video', VIDEO_CARD]
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
                url_webpage = 'https://www.fibranet.cl/index.php/categoria' \
                              '-producto/{}/?product-page={}'.format(
                                url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
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
        if soup.find('h1', 'product_title'):
            name = soup.find('h1', 'product_title').text
        else:
            name = soup.find('div', 'et_pb_module_inner').text
        sku = soup.find('button', {'name': 'add-to-cart'})['value']
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        price = Decimal(remove_words(soup.find('p', 'price').find('bdi').text))
        picture_urls = [tag['src'] for tag in soup.find('div',
                        'woocommerce-product-gallery').findAll('img')]
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
            picture_urls=picture_urls,

        )
        return [p]
