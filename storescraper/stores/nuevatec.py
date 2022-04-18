from decimal import Decimal
import demjson
import logging
from bs4 import BeautifulSoup
from storescraper.categories import CASE_FAN, COMPUTER_CASE, \
    EXTERNAL_STORAGE_DRIVE, HEADPHONES, KEYBOARD, MICROPHONE, MONITOR, \
    MOTHERBOARD, MOUSE, POWER_SUPPLY, PRINTER, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, STEREO_SYSTEM, STORAGE_DRIVE, USB_FLASH_DRIVE, \
    VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Nuevatec(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            RAM,
            COMPUTER_CASE,
            CASE_FAN,
            POWER_SUPPLY,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MOUSE,
            KEYBOARD,
            USB_FLASH_DRIVE,
            PRINTER,
            MICROPHONE,
            HEADPHONES,
            STEREO_SYSTEM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['monitores', MONITOR],
            ['componentes-pc/placas-madres', MOTHERBOARD],
            ['componentes-pc/procesadores', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['componentes-pc/memorias-ram', RAM],
            ['componentes-pc/gabinetes', COMPUTER_CASE],
            ['refrigeracion', CASE_FAN],
            ['componentes-pc/fuentes-de-poder', POWER_SUPPLY],
            ['almacenamiento/discos-duros', STORAGE_DRIVE],
            ['unidades-de-estado-solido-ssd', SOLID_STATE_DRIVE],
            ['discos-duro-externo', EXTERNAL_STORAGE_DRIVE],
            ['mouses', MOUSE],
            ['teclados', KEYBOARD],
            ['pendrive', USB_FLASH_DRIVE],
            ['accesorios-1/impresoras', PRINTER],
            ['microfonos', MICROPHONE],
            ['accesorios-1/audifonos', HEADPHONES],
            ['accesorios-1/parlantes', STEREO_SYSTEM],
            ['cables-y-accesorios/memoria-ram-notebook', RAM],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.nuevatec.cl/{}?' \
                              'page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-block')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.nuevatec.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('form', 'product-form')['action'].split('/')[-1]

        json_data = demjson.decode(soup.find(
            'script', {'type': 'application/ld+json'}).text, strict=False)

        name = json_data['name']
        sku = None
        if 'sku' in json_data:
            sku = json_data['sku']
        description = json_data['description']
        price = Decimal(json_data['offers']['price'])

        stock = 0
        stock_span = soup.find('span', 'product-form-stock')
        if stock_span:
            stock = int(stock_span.text)

        picture_urls = []
        image_container = soup.find('div', 'product-images')
        for image in image_container.findAll('img'):
            picture_urls.append(image['src'])

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
            description=description
        )
        return [p]
