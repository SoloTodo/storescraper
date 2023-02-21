import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MICROPHONE, MOUSE, STORAGE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, SOLID_STATE_DRIVE, HEADPHONES, STEREO_SYSTEM, \
    KEYBOARD, COMPUTER_CASE, CPU_COOLER, POWER_SUPPLY, RAM, MEMORY_CARD, \
    USB_FLASH_DRIVE, GAMING_CHAIR, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, \
    session_with_proxy


class PcInfinity(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            HEADPHONES,
            STEREO_SYSTEM,
            KEYBOARD,
            COMPUTER_CASE,
            CPU_COOLER,
            POWER_SUPPLY,
            RAM,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            GAMING_CHAIR,
            CASE_FAN,
            MICROPHONE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento/discos-duros', STORAGE_DRIVE],
            ['almacenamiento/discos-externos', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento/discos-solidos', SOLID_STATE_DRIVE],
            ['audio/audifonos', HEADPHONES],
            ['audio/audifonos-gamer', HEADPHONES],
            ['audio/microfonos', MICROPHONE],
            ['audio/parlantes', STEREO_SYSTEM],
            ['gabinetes', COMPUTER_CASE],
            ['memorias/memorias-flash', MEMORY_CARD],
            ['memorias/memorias-notebook', RAM],
            ['memorias/memorias-pc', RAM],
            ['memorias/pendrives', USB_FLASH_DRIVE],
            ['mouse-mouse', MOUSE],
            ['mouse/mouse-gamer', MOUSE],
            ['teclados', KEYBOARD],
            ['refrigeracion/ventiladores-para-cpu', CPU_COOLER],
            ['refrigeracion/ventiladores-para-gabinetes', CASE_FAN],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['zona-gamer/parlantes-gamer', STEREO_SYSTEM],
            ['sillas-y-escritorios-gamer', GAMING_CHAIR],
            ['mouse-gamer', MOUSE],
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

                url_webpage = 'https://www.pc-infinity.cl/categoria-producto' \
                    '/{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if len(product_containers) == 0:
                    if page == 1:
                        logging.warning('empty category: ' + url_extension)
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

        key = soup.find('link', {'rel': 'shortlink'})[
            'href'].split('=')[-1]

        name = soup.find('h1', 'product_title').text.strip()
        sku = soup.find('span', 'sku').text.strip()

        offer_price = Decimal(remove_words(
            soup.find('div', 'wds-first').find('span').text))
        normal_price = Decimal(remove_words(
            soup.find('div', 'wds-second').find('span').text))

        if normal_price < offer_price:
            normal_price = offer_price

        input_qty = soup.find('input', 'qty')
        if input_qty:
            if 'max' in input_qty.attrs and input_qty['max']:
                stock = int(input_qty['max'])
            else:
                stock = -1
        else:
            stock = 0

        description = html_to_markdown(
            soup.find('div', {'id': 'tab-description'}).text)

        picture_container = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        picture_urls = []
        for i in picture_container.findAll('img'):
            picture_urls.append(i['src'])

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
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
