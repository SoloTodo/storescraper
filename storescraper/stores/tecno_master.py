import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, PROCESSOR, VIDEO_CARD, \
    SOLID_STATE_DRIVE, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, RAM, \
    POWER_SUPPLY, COMPUTER_CASE, CPU_COOLER, HEADPHONES, MONITOR, MOUSE, \
    STEREO_SYSTEM, KEYBOARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class TecnoMaster(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            RAM,
            POWER_SUPPLY,
            COMPUTER_CASE,
            CPU_COOLER,
            HEADPHONES,
            MONITOR,
            MOUSE,
            STEREO_SYSTEM,
            KEYBOARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['placas-madres', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['sdd', SOLID_STATE_DRIVE],
            ['hdd', STORAGE_DRIVE],
            ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['memorias-ram', RAM],
            ['www-tecno-master-cl-fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['refrigeracion-ventiladores', CPU_COOLER],
            ['audifonos', HEADPHONES],
            ['monitores', MONITOR],
            ['mouse', MOUSE],
            ['parlantes', STEREO_SYSTEM],
            ['teclados', KEYBOARD]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            local_urls = []
            done = False
            while not done:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://tecno-master.cl/{}/page/{}'.format(
                    url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('ul', 'wc-block-grid__products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll(
                        'li', 'wc-block-grid__product'):
                    product_url = container.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break
                    local_urls.append(product_url)
                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name_tag = soup.find('h1', 'product_title')

        if not name_tag:
            return []

        name = name_tag.text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        elif soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = -1
        price_container = soup.find('p', 'price')
        if price_container.find('ins'):
            price = Decimal(remove_words(price_container.find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        picture_urls = [tag['src'] for tag in soup.find('div',
                                                        'woocommerce-product'
                                                        '-gallery')
                        .findAll('img')]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
