import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STORAGE_DRIVE, HEADPHONES, POWER_SUPPLY, \
    COMPUTER_CASE, MONITOR, RAM, MOUSE, MOTHERBOARD, PROCESSOR, CPU_COOLER, \
    GAMING_CHAIR, VIDEO_CARD, KEYBOARD, GAMING_DESK, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class SmartGaming(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            HEADPHONES,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MONITOR,
            RAM,
            MOUSE,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            GAMING_CHAIR,
            VIDEO_CARD,
            KEYBOARD,
            GAMING_DESK,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento', STORAGE_DRIVE],
            ['audio', HEADPHONES],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['monitores', MONITOR],
            ['memorias', RAM],
            ['mouse', MOUSE],
            ['placas-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['refrigeracion', CPU_COOLER],
            ['sillas', GAMING_CHAIR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['teclados', KEYBOARD],
            ['escritorios', GAMING_DESK],
            ['microfonos', MICROPHONE]
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://www.smartgaming.cl/categoria-producto' \
                              '/{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'classic')

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
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            if soup.find('input', {'name': 'quantity'}):
                stock = -1
            else:
                stock = 0
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))

        picture_urls = [tag['data-large_image'] for tag in
                        soup.find('div', 'woocommerce-product-gallery').find(
                            'div', 'slider').findAll('img')]

        description = html_to_markdown(str(soup.find(
            'div', 'woocommerce-product-details__short-description')
        ) + str(soup.find('div', 'woocommerce-Tabs-panel--description')))

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
