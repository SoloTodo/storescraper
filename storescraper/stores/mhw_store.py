import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, STORAGE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, PROCESSOR, RAM, MOTHERBOARD, KEYBOARD, MOUSE, \
    KEYBOARD_MOUSE_COMBO, HEADPHONES, STEREO_SYSTEM, COMPUTER_CASE, \
    VIDEO_CARD, CPU_COOLER, MONITOR, GAMING_CHAIR, POWER_SUPPLY, MICROPHONE, \
    NOTEBOOK
from storescraper.product import Product

from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MHWStore(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            PROCESSOR,
            RAM,
            MOTHERBOARD,
            KEYBOARD,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            HEADPHONES,
            STEREO_SYSTEM,
            COMPUTER_CASE,
            VIDEO_CARD,
            CPU_COOLER,
            MONITOR,
            GAMING_CHAIR,
            POWER_SUPPLY,
            MICROPHONE,
            NOTEBOOK,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['8-ssd-discos-estado-solido', SOLID_STATE_DRIVE],
            ['9-hdd-disco-mecanico', STORAGE_DRIVE],
            ['42-discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['4-procesadores', PROCESSOR],
            ['5-memorias-ram', RAM],
            ['6-placas-madre', MOTHERBOARD],
            ['15-teclados', KEYBOARD],
            ['16-mouses', MOUSE],
            ['17-combos-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['19-auriculares', HEADPHONES],
            ['20-parlantes', STEREO_SYSTEM],
            ['46-sillas-gamer', GAMING_CHAIR],
            ['24-gabinetes', COMPUTER_CASE],
            ['36-tarjetas-de-video', VIDEO_CARD],
            ['39-cooler-cpu', CPU_COOLER],
            ['44-fuentes-de-poder', POWER_SUPPLY],
            ['47-monitores', MONITOR],
            ['45-microfonos', MICROPHONE],
            ['58-notebooks', NOTEBOOK],
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
                url_webpage = 'https://www.mhwstore.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage, timeout=20).text
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
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'h1').text
        sku = soup.find('input', {'id': 'product_page_product_id'})['value']
        not_stock = soup.find('span', {'id': 'product-availability'}).text
        if 'Fuera de stock' in not_stock:
            stock = 0
        else:
            stock = int(
                soup.find('div', 'product-quantities').find('span')[
                    'data-stock'])
        price = Decimal(soup.find('span', 'price')['content'])
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'images-container').findAll('img')
                        if tag['src']]
        print(picture_urls)
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
