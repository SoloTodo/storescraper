import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, PROCESSOR, MOTHERBOARD, \
    STORAGE_DRIVE, RAM, POWER_SUPPLY, CPU_COOLER, COMPUTER_CASE, KEYBOARD, \
    HEADPHONES, PRINTER, NOTEBOOK, MONITOR, STEREO_SYSTEM, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class MegaDriveStore(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_CARD,
            PROCESSOR,
            MOTHERBOARD,
            STORAGE_DRIVE,
            RAM,
            POWER_SUPPLY,
            CPU_COOLER,
            COMPUTER_CASE,
            KEYBOARD,
            HEADPHONES,
            PRINTER,
            NOTEBOOK,
            MONITOR,
            STEREO_SYSTEM,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['11-tarjetas-de-video', VIDEO_CARD],
            ['12-procesadores-amd', PROCESSOR],
            ['13-procesadores-intel', PROCESSOR],
            ['14-placas-madres-amd', MOTHERBOARD],
            ['15-placas-madres-intel', MOTHERBOARD],
            ['16-discos-duros', STORAGE_DRIVE],
            ['17-memorias', RAM],
            ['18-fuentes-de-poder', POWER_SUPPLY],
            ['35-ventiladores', CASE_FAN],
            ['36-disipador-cpu', CPU_COOLER],
            ['37-refrigeracion-liquida', CPU_COOLER],
            ['20-gabinetes', COMPUTER_CASE],
            ['22-mouse-y-teclados', KEYBOARD],
            ['74-audifonos', HEADPHONES],
            ['26-impresoras', PRINTER],
            ['54-notebook', PRINTER],
            ['70-monitores', MONITOR],
            ['73-parlantes', STEREO_SYSTEM],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://megadrivestore.cl/es/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find(
                    'section', {'id': 'products'}).findAll('article')
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
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_container = soup.find('div', 'row product_container')
        name = product_container.find('h1', 'product_name').text
        sku = product_container.find('input', {'name': 'id_product'})['value']
        offer_price = Decimal(remove_words(
            product_container.find('div', 'product-prices')
            .find('span', 'price')['content']))
        normal_price = (offer_price / Decimal('0.95')).quantize(0)
        stock_container = product_container.find('span', {
            'id': 'product-availability'}).text.strip().split('\n')[-1].strip()
        if stock_container == 'Producto en Stock' or stock_container == \
                'Últimas unidades en stock':
            stock = -1
        else:
            stock = 0
        picture_urls = [tag.find('img')['src'] for tag in
                        product_container.findAll('li', 'thumb-container')]
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
