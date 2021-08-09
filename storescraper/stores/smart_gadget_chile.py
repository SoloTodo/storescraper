import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MONITOR, RAM, VIDEO_CARD, \
    PROCESSOR, COMPUTER_CASE, KEYBOARD_MOUSE_COMBO, SOLID_STATE_DRIVE, \
    TABLET, HEADPHONES, VIDEO_GAME_CONSOLE, GAMING_CHAIR, MOTHERBOARD, \
    POWER_SUPPLY, KEYBOARD, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class SmartGadgetChile(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            MONITOR,
            RAM,
            VIDEO_CARD,
            PROCESSOR,
            COMPUTER_CASE,
            KEYBOARD_MOUSE_COMBO,
            SOLID_STATE_DRIVE,
            TABLET,
            HEADPHONES,
            VIDEO_GAME_CONSOLE,
            GAMING_CHAIR,
            MOTHERBOARD,
            POWER_SUPPLY,
            KEYBOARD,
            WEARABLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebook/nuevos', NOTEBOOK],
            ['notebook/reacondicionados', NOTEBOOK],
            ['consolas', VIDEO_GAME_CONSOLE],
            ['gadget', MONITOR],
            ['ram', RAM],
            ['tarjetas-de-video', VIDEO_CARD],
            ['procesadores', PROCESSOR],
            ['gabinete', COMPUTER_CASE],
            ['placas-madre', MOTHERBOARD],
            ['fuente-de-poder-1', POWER_SUPPLY],
            ['teclados-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['teclados', KEYBOARD],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['tablet', TABLET],
            ['accesorios-gamer', GAMING_CHAIR],
            ['audifonos', HEADPHONES],
            ['smart-watch', WEARABLE],
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
                url_webpage = 'https://www.smartgadgetchile.cl/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.smartgadgetchile.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-form_title').text
        sku = soup.find('form', 'product-form')['action'].split('/')[-1]

        description_tag = soup.find('div', {'id': 'product-tabs_content'})
        description = html_to_markdown(str(description_tag))

        if 'LLEGADA' in description.upper():
            # Preventa
            stock = 0
        elif soup.find('meta', {'content': 'instock'}):
            stock = -1
        else:
            stock = 0

        price = Decimal(
            remove_words(
                soup.find('span', 'product-form_price').text.split()[0]))
        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'owl-carousel').findAll('img')]
        if 'reacondicionado' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

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
            condition=condition,
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
