import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.categories import HEADPHONES, SOLID_STATE_DRIVE, \
    MOUSE, KEYBOARD, CPU_COOLER, COMPUTER_CASE, \
    POWER_SUPPLY, RAM, MONITOR, MOTHERBOARD, \
    PROCESSOR, VIDEO_CARD, STEREO_SYSTEM, STORAGE_DRIVE
from storescraper.utils import session_with_proxy, remove_words


class EliteCenter(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            STEREO_SYSTEM,
            STORAGE_DRIVE,
            MOUSE,
            KEYBOARD,
            SOLID_STATE_DRIVE,
            CPU_COOLER,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios-gamer', STEREO_SYSTEM],
            ['almacenamiento', STORAGE_DRIVE],
            ['audifonos-2', HEADPHONES],
            ['disco-duro-pcs', STORAGE_DRIVE],
            ['disco-estado-solido', SOLID_STATE_DRIVE],
            ['disipadores', CPU_COOLER],
            ['fuente-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['memorias-ram', RAM],
            ['monitores', MONITOR],
            ['mouse-2', MOUSE],
            ['placas-madres', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['tarjeta-de-video', VIDEO_CARD],
            ['tarjetas-de-video', VIDEO_CARD],
            ['teclados-2', KEYBOARD],

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

                url_webpage = 'https://elitecenter.cl/product-category/{}/' \
                              '?orderby=popularity&paged={}'.format(
                                url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-small')
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-title').text
        sku = soup.find('button', 'single_add_to_cart_button')['value']
        part_number_container = soup.find('span', {'id': '_sku'})
        if part_number_container:
            part_number = part_number_container.text.strip()
        else:
            part_number = None
        stock = int(soup.find('p', 'stock').text.split()[0])
        normal_price = Decimal(
            remove_words(
                soup.find('div', 'product-main').findAll('bdi')[-1].text))
        offer_price = normal_price
        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div', 'product-gallery').findAll('img')]
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
