from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import *
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, \
    session_with_proxy


class Progaming(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            USB_FLASH_DRIVE,
            MONITOR,
            CPU_COOLER,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            PROCESSOR,
            VIDEO_CARD,
            HEADPHONES,
            MICROPHONE,
            STEREO_SYSTEM,
            MOUSE,
            GAMING_CHAIR,
            KEYBOARD,
            MEMORY_CARD,
            WEARABLE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computacion/almacenamiento/discos-y-accesorios',
             SOLID_STATE_DRIVE],
            ['computacion/almacenamiento/pen-drives', USB_FLASH_DRIVE],
            ['computacion/monitores-y-accesorios/monitores', MONITOR],
            ['computacion/componentes-de-pc/coolers-y-ventiladores',
             CPU_COOLER],
            ['computacion/componentes-de-pc/fuentes-de-poder', POWER_SUPPLY],
            ['computacion/componentes-de-pc/gabinetes', COMPUTER_CASE],
            ['computacion/componentes-de-pc/memorias-ram', RAM],
            ['computacion/componentes-de-pc/procesadores', PROCESSOR],
            ['computacion/componentes-de-pc/tarjetas', VIDEO_CARD],
            ['electronica-audio-y-video/audio/audifonos-audio', HEADPHONES],
            ['electronica-audio-y-video/audio/microfonos', MICROPHONE],
            ['electronica-audio-y-video/audio/parlantes-portatiles',
             STEREO_SYSTEM],
            ['electronica-audio-y-video/audio/parlantes-y-subwoofers',
             STEREO_SYSTEM],
            ['electronica-audio-y-video/parlantes', STEREO_SYSTEM],
            ['gaming-y-streaming/audifonos', HEADPHONES],
            ['gaming-y-streaming/mouse', MOUSE],
            ['gaming-y-streaming/sillas-y-sillones', GAMING_CHAIR],
            ['gaming-y-streaming/teclados-fisicos', KEYBOARD],
            ['otras-categorias/accesorios-para-celulares/memorias',
             MEMORY_CARD],
            ['otras-categorias/handies-y-dispositivos-moviles/smartwatches',
             WEARABLE],
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
                url_webpage = 'https://www.progaming.cl/categoria-producto/' \
                    '{}/page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'product')
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

        key = soup.find('link', {'rel': 'shortlink'})[
            'href'].split('=')[-1]

        name = soup.find('h3', 'product_title').text.strip()
        sku = soup.find('span', 'sku').text.strip()

        offer_price = Decimal(remove_words(
            soup.find('h3', {'id': 'precio2'}).text))
        normal_p = soup.find('p', 'price')
        normal_ins = normal_p.find('ins')
        if normal_ins:
            normal_price = Decimal(
                remove_words(normal_ins.text))
        else:
            normal_price = Decimal(
                remove_words(normal_p.find('bdi').text))

        stock = int(soup.find('input', 'qty')['value'])

        picture_container = soup.find(
            'figure', 'woocommerce-product-gallery__wrapper')
        picture_urls = []
        for a in picture_container.findAll('a'):
            picture_urls.append(a['href'])

        description = html_to_markdown(
            soup.find('div', {'id': 'tab-description'}).text)

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
            description=description
        )
        return [p]
