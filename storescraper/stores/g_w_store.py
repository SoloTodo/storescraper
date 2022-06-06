import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, COMPUTER_CASE, RAM, \
    PROCESSOR, VIDEO_CARD, MOTHERBOARD, KEYBOARD, POWER_SUPPLY, CPU_COOLER, \
    MONITOR, MOUSE, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class GWStore(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            MOTHERBOARD,
            COMPUTER_CASE,
            POWER_SUPPLY,
            RAM,
            MOUSE,
            KEYBOARD,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MONITOR,
            CPU_COOLER,
            MICROPHONE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['16-procesadores', PROCESSOR],
            ['36-refrigeracion-', CPU_COOLER],
            ['21-placas-madres', MOTHERBOARD],
            ['27-memorias-ram', RAM],
            ['11-hdd', STORAGE_DRIVE],
            ['12-sdd', SOLID_STATE_DRIVE],
            ['13-ssd-m2', SOLID_STATE_DRIVE],
            ['14-nvme', SOLID_STATE_DRIVE],
            ['15-disco-externo', EXTERNAL_STORAGE_DRIVE],
            ['35-tarjetas-de-video', VIDEO_CARD],
            ['26-fuentes-de-poder', POWER_SUPPLY],
            ['28-gabinete', COMPUTER_CASE],
            ['30-mouse', MOUSE],
            ['31-teclados', KEYBOARD],
            ['32-microfonos', MICROPHONE],
            ['58-monitor', MONITOR],
        ]
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://gwstore.cl/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'article', 'product-miniature')
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
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key_input = soup.find('input', {'id': 'product_page_product_id'})
        print(key_input)
        if not key_input:
            return []

        key = key_input['value']

        name = soup.find('h1', 'product-name').text.strip()
        price = Decimal(soup.find('span', 'price')['content'])

        if soup.find('button', 'add-to-cart'):
            stock_div = soup.find('div', 'product-quantities')
            if stock_div:
                stock = int(stock_div.find('span')['data-stock'])
            else:
                stock = -1
        else:
            stock = 0

        description = html_to_markdown(
            soup.find('div', 'product-description').text)
        sku = soup.find('span', {'itemprop': 'sku'}).text

        picture_urls = []
        picture_container = soup.find('ul', 'product-images')
        for image in picture_container.findAll('img'):
            picture_urls.append(image['data-image-large-src'])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
