import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, STORAGE_DRIVE, \
    POWER_SUPPLY, RAM, COMPUTER_CASE, MONITOR, MOTHERBOARD, PROCESSOR, \
    CPU_COOLER, MOUSE, KEYBOARD, VIDEO_CARD, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Enarix(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            RAM,
            COMPUTER_CASE,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            MOUSE,
            KEYBOARD,
            VIDEO_CARD,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-pc/almacenamiento/unidad-estado-solido-ssd',
             SOLID_STATE_DRIVE],
            ['componentes-pc/almacenamiento/hdd', STORAGE_DRIVE],
            ['componentes-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-pc/memoria-ram', RAM],
            ['gabinetes-gamer', COMPUTER_CASE],
            ['monitores', MONITOR],
            ['componentes-pc/placas-madres', MOTHERBOARD],
            ['componentes-pc/procesadores', PROCESSOR],
            ['componentes-pc/refrigeracion-y-ventiladores', CPU_COOLER],
            ['componentes-pc/tarjeta-de-video', VIDEO_CARD],
            ['accessorios/mouse', MOUSE],
            ['accessorios/teclados', KEYBOARD],
            ['accessorios/microfonos', MICROPHONE]
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
                url_webpage = 'https://tienda.enarix.cl/product-category/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'products')
                if soup.find('div', 'info-404'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll('li', 'product'):
                    product_url = \
                        container.find('a', 'woocommerce-LoopProduct-link')[
                            'href']
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
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        stock_tag = soup.find('input', {'name': 'quantity'})
        if stock_tag:
            if 'max' in stock_tag.attrs:
                stock = int(stock_tag['max'])
            else:
                stock = 1
        else:
            stock = 0
        price_container = soup.find('span', 'electro-price')
        if price_container.find('ins'):
            offer_price = remove_words(price_container.find('ins').text)
        else:
            offer_price = remove_words(price_container.find('bdi').text)

        offer_price = Decimal(offer_price)
        normal_price = offer_price * Decimal('1.04')

        picture_urls = []
        description = html_to_markdown(str(soup.find(
            'div', 'woocommerce-Tabs-panel--description')))
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            Decimal(offer_price),
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
