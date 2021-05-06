import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PRINTER, MOTHERBOARD, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, VIDEO_CARD, MONITOR, KEYBOARD_MOUSE_COMBO, \
    COMPUTER_CASE, EXTERNAL_STORAGE_DRIVE, POWER_SUPPLY, HEADPHONES, \
    CPU_COOLER, GAMING_CHAIR, KEYBOARD, NOTEBOOK, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class KillStore(Store):
    @classmethod
    def categories(cls):
        return [
            PRINTER,
            MOTHERBOARD,
            PROCESSOR,
            RAM,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            COMPUTER_CASE,
            EXTERNAL_STORAGE_DRIVE,
            POWER_SUPPLY,
            HEADPHONES,
            CPU_COOLER,
            GAMING_CHAIR,
            KEYBOARD,
            NOTEBOOK,
            VIDEO_GAME_CONSOLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['230-impresion', PRINTER],
            ['280-placas-madre', MOTHERBOARD],
            ['279-procesadores', PROCESSOR],
            ['277-memorias-ram', RAM],
            ['278-discos-internos', SOLID_STATE_DRIVE],
            ['281-tarjetas-de-video', VIDEO_CARD],
            ['283-monitores', MONITOR],
            ['286-teclado-mouse', KEYBOARD_MOUSE_COMBO],
            ['282-fuentes', POWER_SUPPLY],
            ['370-gabinetes', COMPUTER_CASE],
            ['285-discos-externos', EXTERNAL_STORAGE_DRIVE],
            ['104-audifonos', HEADPHONES],
            ['369-refrigeracion-y-ventiladores', CPU_COOLER],
            ['335-sillas', GAMING_CHAIR],
            ['389-teclados', KEYBOARD],
            ['388-notebooks', NOTEBOOK],
            ['401-consolas', VIDEO_GAME_CONSOLE],
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
                url_webpage = 'https://www.killstore.cl/{}?page={}'.format(
                    url_extension, page)
                res = session.get(url_webpage)

                # Killstore may block connections which result en empty pages
                # with seemingly no products, so check that the response code
                # is OK
                assert res.status_code == 200

                soup = BeautifulSoup(res.text, 'html.parser')
                product_containers = soup.findAll('article',
                                                  'js-product-miniature')
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

        # Killstore may block connections which result en empty pages, so
        # check the status code of the response
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('meta', {'property': 'og:name_product'})['content']
        sku = soup.find('meta', {'property': 'og:id_product'})['content']
        price_container = list(map(lambda x: Decimal(remove_words(x.text)),
                                   soup.find('div', 'current-price').findAll(
                                       'span', 'price')))
        normal_price = max(price_container)
        offer_price = min(price_container)
        stock_container = soup.find('div', 'available-stock-list')
        if stock_container and len(
                stock_container.findAll('span', 'fa fa-check')):
            stock = -1
        else:
            stock = 0

        picture_urls = [tag['src'] for tag in
                        soup.find('ul', 'product-images').findAll('img') if
                        tag['src'].startswith('http')]

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
            picture_urls=picture_urls
        )
        return [p]
