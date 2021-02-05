import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, RAM, POWER_SUPPLY, \
    VIDEO_CARD, SOLID_STATE_DRIVE, CPU_COOLER, PROCESSOR, MONITOR, \
    COMPUTER_CASE, HEADPHONES, MOUSE, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class BulldogPc(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            RAM,
            MOTHERBOARD,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            CPU_COOLER,
            PROCESSOR,
            MONITOR,
            COMPUTER_CASE,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['productos/almacenamiento', SOLID_STATE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['productos/gabinetes', COMPUTER_CASE],
            ['memorias', RAM],
            ['productos/monitores', MONITOR],
            ['productos/placas-madre', MOTHERBOARD],
            ['productos/refrigeracion', CPU_COOLER],
            ['productos/perifericos/audifonos', HEADPHONES],
            ['productos/perifericos/ratones', MOUSE],
            ['productos/perifericos/teclados', KEYBOARD],
            ['productos/procesadores', PROCESSOR],
            ['productos/tarjetas-de-video', VIDEO_CARD],
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
                url_webpage = 'https://www.bulldogpc.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-holder')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.bulldogpc.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-name').text
        sku_container = soup.find(
            'meta', property='og:image')['content']
        sku = re.search(r"/(\d+)/", sku_container).group(1)
        unavailable_tag = soup.find(
            'div', 'form-group product-stock product-out-stock row visible')
        if unavailable_tag:
            stock = 0
        else:
            stock = int(soup.find('div', {'id': 'stock'}).
                        find('span', 'product-form-stock').text)
        price = Decimal(
            remove_words(soup.find("span", "product-form-price").text))
        picture_containers = soup.find("div", "col-12 product-page-thumbs "
                                              "space no-padding")
        if picture_containers:
            picture_urls = [tag['src'].split("?")[0] for tag in
                            picture_containers.findAll('img')]
        else:
            picture_urls = [soup.find('div', 'main-product-image')
                                .find('img')['src']]
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
