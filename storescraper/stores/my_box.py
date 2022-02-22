import logging
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR, KEYBOARD, VIDEO_CARD, \
    PROCESSOR, MOTHERBOARD, RAM, STORAGE_DRIVE, CPU_COOLER, POWER_SUPPLY, \
    COMPUTER_CASE, MONITOR, HEADPHONES, STEREO_SYSTEM, MICROPHONE, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class MyBox(Store):
    @classmethod
    def categories(cls):
        return [
            KEYBOARD,
            GAMING_CHAIR,
            VIDEO_CARD,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            STORAGE_DRIVE,
            CPU_COOLER,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MONITOR,
            HEADPHONES,
            STEREO_SYSTEM,
            MICROPHONE,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['20-teclados-mouse', KEYBOARD],
            ['25-sillas-gamer', GAMING_CHAIR],
            ['68-tarjeta-de-video', VIDEO_CARD],
            ['64-procesador', PROCESSOR],
            ['65-placa-madre', MOTHERBOARD],
            ['66-memoria-ram', RAM],
            ['67-almacenamiento', STORAGE_DRIVE],
            ['92-enfriamiento-refrigeracion', CPU_COOLER],
            ['63-fuentes-de-poder', POWER_SUPPLY],
            ['62-gabinetes', COMPUTER_CASE],
            ['28-monitor', MONITOR],
            ['21-audifonos-headset', HEADPHONES],
            ['22-parlantes', STEREO_SYSTEM],
            ['24-microfonos', MICROPHONE],
            ['89-ventiladores-fans', CASE_FAN],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overlfow: ' + url_extension)

                url_webpage = 'https://mybox.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)

                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'js-product-'
                                                         'miniature-wrapper')

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
        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('input', {'name': 'id_product'})['value']
        if soup.find('div', 'stock-disponible').text.strip() == 'No hay ' \
                                                                'suficientes' \
                                                                ' productos ' \
                                                                'en stock':
            stock = 0
        else:
            stock = -1
        normal_price = Decimal(
            soup.find('span', 'current-price').find('span', 'product-price')[
                'content'])
        offer_price = Decimal(remove_words(
            soup.find('span', 'transf-price').text.strip().split()[0]))
        if normal_price == 0 or offer_price == 0:
            stock = 0
        picture_urls = [tag['src'] for tag in soup.find('div',
                                                        'images-container').
                        findAll('img') if tag.get('src')]
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
            picture_urls=picture_urls,
        )
        return [p]
