import logging
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR, KEYBOARD, VIDEO_CARD, \
    PROCESSOR, MOTHERBOARD, RAM, STORAGE_DRIVE, CPU_COOLER, POWER_SUPPLY, \
    COMPUTER_CASE, MONITOR, HEADPHONES, STEREO_SYSTEM, MICROPHONE, CASE_FAN, \
    UPS, USB_FLASH_DRIVE, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


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
            UPS,
            USB_FLASH_DRIVE,
            NOTEBOOK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['64-procesador', PROCESSOR],
            ['68-tarjeta-de-video', VIDEO_CARD],
            ['65-placa-madre', MOTHERBOARD],
            ['66-memoria-ram', RAM],
            ['67-almacenamiento', STORAGE_DRIVE],
            ['92-enfriamiento-refrigeracion', CPU_COOLER],
            ['63-fuentes-de-poder', POWER_SUPPLY],
            ['62-gabinetes', COMPUTER_CASE],
            ['89-ventiladores-fans', CASE_FAN],
            ['91-respaldo-energetico-ups', UPS],
            ['28-monitor', MONITOR],
            ['20-teclados-mouse', KEYBOARD],
            ['21-audifonos-headset', HEADPHONES],
            ['22-parlantes', STEREO_SYSTEM],
            ['26-iluminacion-rgb', CASE_FAN],
            ['210-memorias-sd-microsd-y-pendrives', USB_FLASH_DRIVE],
            ['16-notebook', NOTEBOOK],
            ['25-sillas-gamer', GAMING_CHAIR],
            ['24-microfonos', MICROPHONE],
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

                url_webpage = 'https://mybox.cl/{}'.format(
                    url_extension)

                if page > 1:
                    url_webpage += '?page={}'.format(page)
                print(url_webpage)

                response = session.get(url_webpage)

                if response.url != url_webpage:
                    print(response.url, url_webpage)
                    if page == 1:
                        logging.warning('Empy category: ' + url_webpage)
                    break

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
        key = soup.find('input', {'name': 'id_product'})['value']
        span_sku = soup.find('span', {'itemprop': 'sku'})
        if span_sku:
            sku = span_sku.text.strip()
        else:
            sku = None
        if soup.find('button', 'add-to-cart'):
            stock = -1
        else:
            stock = 0
        normal_price = Decimal(
            soup.find('meta', {'property': 'product:price:amount'})['content'])
        offer_price = (normal_price * Decimal('0.95')).quantize(0)

        picture_urls = [soup.find('meta', {'property': 'og:image'})['content']]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
        )
        return [p]
