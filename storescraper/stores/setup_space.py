import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import RAM, MONITOR, MOTHERBOARD, PROCESSOR, \
    SOLID_STATE_DRIVE, VIDEO_CARD, STORAGE_DRIVE, NOTEBOOK, WEARABLE, \
    KEYBOARD, COMPUTER_CASE
from storescraper.utils import session_with_proxy, remove_words


class SetupSpace(Store):
    @classmethod
    def categories(cls):
        return [
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            NOTEBOOK,
            STORAGE_DRIVE,
            WEARABLE,
            KEYBOARD,
            COMPUTER_CASE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['ram', RAM],
            ['monitores', MONITOR],
            ['tarjeta-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['ssd', SOLID_STATE_DRIVE],
            ['m2-sata', SOLID_STATE_DRIVE],
            ['m2-nvme', SOLID_STATE_DRIVE],
            ['hdd', STORAGE_DRIVE],
            ['tarjetas-graficas', VIDEO_CARD],
            ['notebooks', NOTEBOOK],
            ['apple-watch-1', WEARABLE],
            ['apple-watch', KEYBOARD],
            ['gabinetes', COMPUTER_CASE],
        ]

        session = session_with_proxy(extra_args)
        products_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.setupspace.cl/{}?page={}' \
                    .format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_webpage)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    products_urls.append('https://www.setupspace.cl' +
                                         product_url)
                page += 1

        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'page-header').text
        sku = soup.find('span', 'sku_elem').text.strip()
        price = Decimal(
            remove_words(soup.find('span', {'id': 'product-form-price'}).text))

        if soup.find('meta', {'property': 'product:availability'})['content'] \
                != 'instock':
            stock = 0
        else:
            stock = int(soup.find('input', {'id': 'input-qty'})['max'])

        if soup.find('div', 'owl-thumbs mt-2 mr-n2'):
            picture_urls = [tag['src'] for tag in
                            soup.find('div', 'owl-thumbs mt-2 mr-n2').findAll(
                                'img')]
        else:
            picture_urls = [
                soup.find('div', 'product-images').find('img')['src']]

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
