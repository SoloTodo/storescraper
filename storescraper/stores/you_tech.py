import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, HEADPHONES, \
    KEYBOARD_MOUSE_COMBO, MONITOR, MOUSE, KEYBOARD, POWER_SUPPLY, PROCESSOR, \
    MOTHERBOARD, CPU_COOLER, SOLID_STATE_DRIVE, EXTERNAL_STORAGE_DRIVE, \
    STORAGE_DRIVE, RAM, MEMORY_CARD, USB_FLASH_DRIVE, CELL, WEARABLE, \
    PRINTER, UPS, GAMING_CHAIR, COMPUTER_CASE, VIDEO_CARD, TABLET, \
    ALL_IN_ONE, GAMING_DESK, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class YouTech(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            MONITOR,
            MOUSE,
            KEYBOARD,
            POWER_SUPPLY,
            PROCESSOR,
            MOTHERBOARD,
            CPU_COOLER,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            RAM,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            CELL,
            WEARABLE,
            PRINTER,
            UPS,
            GAMING_CHAIR,
            COMPUTER_CASE,
            VIDEO_CARD,
            TABLET,
            ALL_IN_ONE,
            GAMING_DESK,
            VIDEO_GAME_CONSOLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['67906_67934', NOTEBOOK],
            ['67906_67979', NOTEBOOK],
            ['67906_67935', ALL_IN_ONE],
            ['67824_67897', HEADPHONES],
            ['67824_67850', KEYBOARD_MOUSE_COMBO],
            ['68001', MONITOR],
            ['67824_67846', MOUSE],
            ['67824_67890', KEYBOARD],
            ['67861_67930', COMPUTER_CASE],
            ['67861_67869', POWER_SUPPLY],
            ['67861_67929', PROCESSOR],
            ['67861_67919', VIDEO_CARD],
            ['67861_67955', MOTHERBOARD],
            ['67861_67949', CPU_COOLER],
            ['67829_67931', SOLID_STATE_DRIVE],
            ['67829_67873', EXTERNAL_STORAGE_DRIVE],
            ['67829_67872', STORAGE_DRIVE],
            ['67863_67865', RAM],
            ['67863_67866', RAM],
            ['67863_67928', MEMORY_CARD],
            ['67863_67864', USB_FLASH_DRIVE],
            ['67833_67927', CELL],
            ['67833_67982', TABLET],
            ['67833_67951', WEARABLE],
            ['67833_67966', WEARABLE],
            ['67851', PRINTER],
            ['67822_67857', UPS],
            ['67844', GAMING_CHAIR],
            ['67845', GAMING_DESK],
            ['68010', VIDEO_GAME_CONSOLE],
        ]
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.52.1'
        session.headers['Accept'] = '*/*'

        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.youtech.cl/tienda/index.php?route' \
                              '=product/category&path={}&page={}'. \
                    format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage, verify=False).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-layout')
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
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-name').text.strip()
        key = soup.find('input', {'name': 'product_id'})['value']
        sku = soup.find('td', text='Código del producto:').next.next \
            .text.strip()
        stock_text = soup.find(
            'td', text='Disponibilidad:').next.next.text.strip()
        if stock_text == 'En Stock':
            stock = -1
        else:
            stock = 0

        prices_tag = soup.find('ul', 'product-price')
        normal_price_container = prices_tag.find('li', 'product-tax')
        normal_price = Decimal(remove_words(
            normal_price_container.text.split(':')[1]))
        offer_price_container = prices_tag.find('h2', 'cash-price')
        offer__price = Decimal(remove_words(offer_price_container.text))

        picture_urls = [tag['data-zoom-image'] for tag in
                        soup.find('div', 'additional-images-container')
                            .findAll('img')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer__price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
