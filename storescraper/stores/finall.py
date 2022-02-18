import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import RAM, MOTHERBOARD, VIDEO_CARD, \
    POWER_SUPPLY, SOLID_STATE_DRIVE, MOUSE, HEADPHONES, KEYBOARD, \
    PROCESSOR, COMPUTER_CASE, CPU_COOLER, STORAGE_DRIVE, MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Finall(Store):
    @classmethod
    def categories(cls):
        return [
            RAM,
            MOTHERBOARD,
            VIDEO_CARD,
            POWER_SUPPLY,
            SOLID_STATE_DRIVE,
            MOUSE,
            HEADPHONES,
            KEYBOARD,
            PROCESSOR,
            COMPUTER_CASE,
            CPU_COOLER,
            STORAGE_DRIVE,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['pc/memorias-ram', RAM],
            ['pc/memorias-ram/ddr3', RAM],
            ['pc/memorias-ram/ddr4', RAM],
            ['pc/placa-madre', MOTHERBOARD],
            ['pc/tarjeta-de-video', VIDEO_CARD],
            ['pc/fuente-de-poder', POWER_SUPPLY],
            ['pc/disco-estado-solido-1', SOLID_STATE_DRIVE],
            ['sata', SOLID_STATE_DRIVE],
            ['nvme-pcie', SOLID_STATE_DRIVE],
            ['pc/m2', SOLID_STATE_DRIVE],
            ['mouse', MOUSE],
            ['audifonos', HEADPHONES],
            ['perifericos/teclados', KEYBOARD],
            ['pc/procesadores', PROCESSOR],
            ['pc/gabinetes', COMPUTER_CASE],
            ['pc/refrigeracion', CPU_COOLER],
            ['pc/disco-duro-mecanico', STORAGE_DRIVE],
            ['pc/monitores', MONITOR],
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
                url_webpage = 'https://www.finall.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                if response.status_code == 404:
                    raise Exception('Invalid category: ' + url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div',
                                                  'col-lg-3 col-md-4 col-6')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://www.finall.cl' + product_url)
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
        part_number = soup.find('span', 'sku_elem').text
        if soup.find('span', 'product-form-stock'):
            stock = int(soup.find('span', 'product-form-stock').text)
        else:
            stock = 0
        price_container = soup.findAll('span', {'id': 'product-form-price'})
        normal_price = Decimal(remove_words(price_container[1].text))
        offer_price = Decimal(remove_words(price_container[0].text))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'product-images').findAll('img')]
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
