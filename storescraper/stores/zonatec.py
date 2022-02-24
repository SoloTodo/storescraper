import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, EXTERNAL_STORAGE_DRIVE, COMPUTER_CASE, MOTHERBOARD, \
    PROCESSOR, VIDEO_CARD, CPU_COOLER, POWER_SUPPLY, MONITOR, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Zonatec(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            ALL_IN_ONE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            COMPUTER_CASE,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            CPU_COOLER,
            POWER_SUPPLY,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computadores/notebooks/convencionales', NOTEBOOK],
            ['computadores/notebooks/ultrabooks', NOTEBOOK],
            ['computadores/notebooks/notebooks-gamer', NOTEBOOK],
            ['computadores/todo-en-uno', ALL_IN_ONE],
            ['componentes/almacenamiento/discos-duros-internos',
             STORAGE_DRIVE],
            ['componentes/almacenamiento/discos-de-estado-solido',
             SOLID_STATE_DRIVE],
            ['componentes/almacenamiento/discos-duros-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['componentes/gabinetes', COMPUTER_CASE],
            ['componentes/placas-madres', MOTHERBOARD],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['componentes/refrigeracion', CPU_COOLER],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['perifericos/monitores', MONITOR]
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
                url_webpage = 'https://zonatec.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')
                if not product_containers or soup.find('div', 'info-404'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
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
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        part_number = \
            soup.findAll('div', 'elementor-text-editor elementor-clearfix')[
                1].text.split(': ')[-1]
        stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        price_container = soup.findAll('span',
                                       'woocommerce-Price-amount amount')
        offer_price = Decimal(remove_words(price_container[2].text))
        normal_price = (offer_price * Decimal('1.036')).quantize(0)
        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]
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
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
