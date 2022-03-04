import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MOUSE, GAMING_CHAIR, \
    KEYBOARD, SOLID_STATE_DRIVE, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, \
    MEMORY_CARD, POWER_SUPPLY, COMPUTER_CASE, RAM, PROCESSOR, CPU_COOLER, \
    MOTHERBOARD, VIDEO_CARD, NOTEBOOK, PRINTER, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class JfConnect(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MOUSE,
            GAMING_CHAIR,
            KEYBOARD,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MEMORY_CARD,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            PROCESSOR,
            CPU_COOLER,
            MOTHERBOARD,
            VIDEO_CARD,
            NOTEBOOK,
            PRINTER,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audifonos', HEADPHONES],
            ['mouse', MOUSE],
            ['sillas-gamer', GAMING_CHAIR],
            ['teclados', KEYBOARD],
            ['almacenamiento/ssd', SOLID_STATE_DRIVE],
            ['almacenamiento/hdd', STORAGE_DRIVE],
            ['almacenamiento/externo', EXTERNAL_STORAGE_DRIVE],
            ['pendrive/microsd', MEMORY_CARD],
            ['accesorios/fuente-de-poder', POWER_SUPPLY],
            ['accesorios/gabinetes', COMPUTER_CASE],
            ['memorias', RAM],
            ['procesadores', PROCESSOR],
            ['accesorios/refrigeracion', CPU_COOLER],
            ['tarjetas-madres', MOTHERBOARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['computadores/notebook', NOTEBOOK],
            ['impresoras', PRINTER],
            ['monitores', MONITOR],
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

                url_webpage = 'https://jfconnect.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.find('div', 'col-12 mt-md-0 mt-5')
                if not product_containers or not product_containers.findAll(
                        'div', 'col-md-3'):
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('div', 'col-md-3'):
                    product_url = container.find('a')['href']
                    product_urls.append('https://jfconnect.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-name').text
        sku = soup.find('span', 'sku_elem').text
        price = Decimal(
            remove_words(soup.find('span', 'product-form-price').text))
        if soup.find('span', 'product-form-stock'):
            stock = int(soup.find('span', 'product-form-stock').text)
        else:
            stock = 0
        if soup.find('div', 'col-12 product-page-thumbs space no-padding'):
            picture_urls = [tag['src'] for tag in soup.find('div', 'col-12 '
                            'product-page-thumbs space no-padding'
                                                            ).findAll('img')]
        else:
            picture_urls = [tag['src'] for tag in soup.find('div',
                            'main-product-image').findAll('img')]

        description = html_to_markdown(str(soup.find('div', 'description')))

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
            description=description
        )
        return [p]
