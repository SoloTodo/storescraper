from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, COMPUTER_CASE, CPU_COOLER, \
    GAMING_CHAIR, HEADPHONES, KEYBOARD, MICROPHONE, MONITOR, MOTHERBOARD, \
    MOUSE, NOTEBOOK, POWER_SUPPLY, PRINTER, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, STEREO_SYSTEM, STORAGE_DRIVE, TABLET, UPS, \
    USB_FLASH_DRIVE, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class CSByte(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MICROPHONE,
            STEREO_SYSTEM,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD,
            ALL_IN_ONE,
            NOTEBOOK,
            PRINTER,
            MONITOR,
            MOUSE,
            KEYBOARD,
            GAMING_CHAIR,
            TABLET,
            UPS
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audio/audifonos', HEADPHONES],
            ['audio/microfonos', MICROPHONE],
            ['audio/parlantes', STEREO_SYSTEM],
            ['componentes-armado/almacenamiento/sdd', SOLID_STATE_DRIVE],
            ['componentes-armado/almacenamiento/hdd', STORAGE_DRIVE],
            ['componentes-armado/almacenamiento/usb', USB_FLASH_DRIVE],
            ['componentes-armado/fuente-de-poder', POWER_SUPPLY],
            ['componentes-armado/gabinete', COMPUTER_CASE],
            ['componentes-armado/memoria-ram', RAM],
            ['componentes-armado/placa-madre', MOTHERBOARD],
            ['componentes-armado/procesadores', PROCESSOR],
            ['componentes-armado/refrigeracion', CPU_COOLER],
            ['componentes-armado/tarjetas-de-video', VIDEO_CARD],
            ['computacion/all-in-one', ALL_IN_ONE],
            ['computacion/notebook', NOTEBOOK],
            ['impresoras', PRINTER],
            ['monitores-y-soportes/monitores', MONITOR],
            ['perifericos/mouse', MOUSE],
            ['perifericos/teclado', KEYBOARD],
            ['sillas', GAMING_CHAIR],
            ['tablets', TABLET],
            ['ups', UPS],
            ['zona-gamer/audifonos-zona-gamer', HEADPHONES],
            ['zona-gamer/mouse-zona-gamer', MOUSE],
            ['zona-gamer/teclados', KEYBOARD],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.csbyte.cl/product-category/{}/' \
                    'page/{}/'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'site-content').findAll(
                    'div', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers[-1].findAll(
                        'div', 'product-grid-item'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)

        if response.url != url:
            print(response.url)
            print(url)
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text.strip()

        new_condition_tag = soup.find(
            'a', {'href': 'https://www.csbyte.cl/estado/nuevo/'})
        if new_condition_tag:
            condition = 'https://schema.org/NewCondition'
        else:
            condition = 'https://schema.org/RefurbishedCondition'

        if soup.find('form', 'variations_form'):
            products = []
            variations = json.loads(soup.find('form', 'variations_form')[
                'data-product_variations'])
            for product in variations:
                variation_name = name + ' - ' + ' '.join(
                    product['attributes'].values())
                key = str(product['variation_id'])
                sku = product.get('sku', None)
                if product['max_qty'] == '':
                    stock = 0
                else:
                    stock = product['max_qty']
                price = Decimal(product['display_price'])
                picture_urls = [product['image']['url']]
                p = Product(
                    variation_name,
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
                    condition=condition
                )
                products.append(p)
            return products
        else:
            key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                -1]
            json_data = json.loads(
                soup.findAll('script', {'type': 'application/ld+json'})[-1]
                    .text)['@graph'][1]
            sku = str(json_data['sku'])
            offer = json_data['offers'][0]
            if offer['availability'] == 'http://schema.org/InStock':
                stock_p = soup.find('p', 'stock')
                if stock_p:
                    stock = int(stock_p.text.split()[0])
                else:
                    stock = -1
            else:
                stock = 0
            price = Decimal(offer['price'])
            picture_urls = [json_data['image']]
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
                condition=condition
            )
            return [p]
