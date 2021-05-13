import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MONITOR, RAM, VIDEO_CARD, \
    PROCESSOR, COMPUTER_CASE, KEYBOARD_MOUSE_COMBO, SOLID_STATE_DRIVE, \
    TABLET, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


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
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebook/nuevos', NOTEBOOK],
            ['notebook/reacondicionados', NOTEBOOK],
            ['gadget', MONITOR],
            ['ram', RAM],
            ['tarjetas-de-video', VIDEO_CARD],
            ['procesadores', PROCESSOR],
            ['gabinete', COMPUTER_CASE],
            ['teclados-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['almacenamiento', SOLID_STATE_DRIVE],
            ['tablet', TABLET],
            ['audifonos', HEADPHONES]
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
                product_containers = soup.findAll('div', 'custom-col-4-in-row')
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
        name = soup.find('h1', 'product-title').text
        sku = soup.find('form', {'id': 'addtocart'})['action'].split('/')[-1]
        if soup.find('meta', {'content': 'instock'}):
            stock = -1
        else:
            stock = 0

        price = Decimal(
            remove_words(soup.find('div', {'id': 'current'}).text.split()[0]))
        picture_urls = [tag['src'] for tag in
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
        )
        return [p]
