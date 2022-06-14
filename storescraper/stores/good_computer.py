import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD, PROCESSOR, MOTHERBOARD, RAM, \
    STORAGE_DRIVE, SOLID_STATE_DRIVE, COMPUTER_CASE, POWER_SUPPLY, \
    CPU_COOLER, MONITOR, KEYBOARD, MOUSE, KEYBOARD_MOUSE_COMBO, HEADPHONES, \
    GAMING_CHAIR, MICROPHONE, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class GoodComputer(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_CARD,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            COMPUTER_CASE,
            POWER_SUPPLY,
            CPU_COOLER,
            MONITOR,
            KEYBOARD,
            MOUSE,
            KEYBOARD_MOUSE_COMBO,
            HEADPHONES,
            GAMING_CHAIR,
            MICROPHONE,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-informaticos/tarjetas-de-video', VIDEO_CARD],
            ['componentes-informaticos/procesadores', PROCESSOR],
            ['componentes-informaticos/placas-madre', MOTHERBOARD],
            ['componentes-informaticos/ram', RAM],
            ['componentes-informaticos/discos-duros', STORAGE_DRIVE],
            ['componentes-informaticos/ssd', SOLID_STATE_DRIVE],
            ['componentes-informaticos/gabinetes', COMPUTER_CASE],
            ['componentes-informaticos/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-informaticos/cooler-cpu/refrigeracion-liquida',
             CPU_COOLER],
            ['componentes-informaticos/ventiladores-enfriamiento', CASE_FAN],
            ['componentes-informaticos/cooler-cpu/por-aire', CASE_FAN],
            ['monitores', MONITOR],
            ['perifericos/teclados', KEYBOARD],
            ['perifericos/mouse', MOUSE],
            ['perifericos/combos', KEYBOARD_MOUSE_COMBO],
            ['perifericos/headsets', HEADPHONES],
            ['sillas-gaming', GAMING_CHAIR],
            ['perifericos/microfonos', MICROPHONE]
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
                url_webpage = 'https://www.goodcomputer.cl/categoria' \
                              '-producto/{}/page/{}' \
                    .format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product-warp-item')
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[1]
        stock_container = soup.find('p', 'stock')
        if not stock_container:
            stock = -1
        elif stock_container.text.split()[0] == 'Agotado':
            stock = 0
        else:
            stock = int(stock_container.text.split()[0])
        price_container = soup.find('p', 'price')
        if not price_container.text.strip():
            return []
        if not price_container.find('ins'):
            price = Decimal(remove_words(price_container.text))
        else:
            price = Decimal(remove_words(price_container.find('ins').text))
        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'main-images').findAll(
                            'img')
                        ]
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
