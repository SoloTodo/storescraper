import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, PRINTER, SOLID_STATE_DRIVE, \
    NOTEBOOK, RAM, POWER_SUPPLY, COMPUTER_CASE, MONITOR, GAMING_CHAIR, \
    WEARABLE, HEADPHONES, MOUSE, KEYBOARD, PROCESSOR, STORAGE_DRIVE, \
    VIDEO_CARD, CPU_COOLER, KEYBOARD_MOUSE_COMBO, UPS, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class PcMasterGames(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            SOLID_STATE_DRIVE,
            NOTEBOOK,
            RAM,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MONITOR,
            GAMING_CHAIR,
            WEARABLE,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            PROCESSOR,
            STORAGE_DRIVE,
            VIDEO_CARD,
            CPU_COOLER,
            KEYBOARD_MOUSE_COMBO,
            UPS,
            MICROPHONE,
            PRINTER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['mouse', MOUSE],
            ['teclados', KEYBOARD],
            ['audio', HEADPHONES],
            ['placas-madres-amd', MOTHERBOARD],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['memoria-ram', RAM],
            ['placas-madres-intel', MOTHERBOARD],
            ['procesadores-amd', PROCESSOR],
            ['procesadores-intel', PROCESSOR],
            ['monitores', MONITOR],
            ['disco-duro', STORAGE_DRIVE],
            ['disco-ssd', SOLID_STATE_DRIVE],
            ['computadores', NOTEBOOK],
            ['memoria-ram', RAM],
            ['sillas-gamer', GAMING_CHAIR],
            ['smartwatch', WEARABLE],
            ['tarjeta-de-video', VIDEO_CARD],
            ['ventiladores-y-sistema-de-enfriamiento-componentes', CPU_COOLER],
            ['combos-de-teclado-y-raton', KEYBOARD_MOUSE_COMBO],
            ['ups', UPS],
            ['microfonos', MICROPHONE],
            ['impresoras-y-escaneres', PRINTER],
        ]
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.pcmastergames.cl/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('a', 'product-image-link')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('=')[-1]
        json_htmls = soup.findAll('script', {'type': 'application/ld+json'})
        if len(json_htmls) < 2:
            return []
        second_json = json.loads(json_htmls[1].text)['@graph'][0]
        name = second_json['name']
        description = second_json['description']
        sku = None
        if 'sku' in second_json:
            sku = second_json['sku']
        offer_price = Decimal(second_json['offers'][0]['price'])
        normal_price = offer_price * Decimal(1.035)
        normal_price = normal_price.quantize(Decimal("0.0"))

        picture_urls = []
        figure = soup.find('figure', 'woocommerce-product-gallery__wrapper')
        images = figure.findAll('img')
        for i in images:
            picture_urls.append(i['src'])

        if second_json['offers'][0]['availability'] == \
                'http://schema.org/InStock':
            stock = int(
                soup.find('p', 'stock in-stock wd-style-default').text.split(
                    ' disponibles')[0])
        else:
            stock = 0

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
            description=description
        )

        return [p]
