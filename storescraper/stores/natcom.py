import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, \
    SOLID_STATE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, RAM, MONITOR, NOTEBOOK, \
    KEYBOARD, MOUSE, HEADPHONES, MOTHERBOARD, PROCESSOR, CPU_COOLER, \
    VIDEO_CARD, CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Natcom(Store):
    @classmethod
    def categories(cls):
        return [
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            NOTEBOOK,
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD,
            CASE_FAN,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
            ['discos-duros', STORAGE_DRIVE],
            ['discos-ssd', SOLID_STATE_DRIVE],
            ['certificada', POWER_SUPPLY],
            ['no-certificada', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['ram-pc-escritorio', RAM],
            ['ram-portatiles', RAM],
            ['monitores', MONITOR],
            ['notebooks', NOTEBOOK],
            ['teclados', KEYBOARD],
            ['mouse', MOUSE],
            ['audifonos', HEADPHONES],
            ['placa-madre-amd', MOTHERBOARD],
            ['placa-madre-intel', MOTHERBOARD],
            ['procesadores-amd', PROCESSOR],
            ['procesadores-intel', PROCESSOR],
            ['refrigeracion-liquida', CPU_COOLER],
            ['ventiladores', CASE_FAN],
            ['tarjetas-de-video-amd', VIDEO_CARD],
            ['tarjetas-de-video-nvidia', VIDEO_CARD],

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
                url_webpage = 'https://natcomchile.cl/{}/page/{}/'.format(
                    url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('article', 'w-grid-item')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break
                    local_urls.append(product_url)
                page += 1
            product_urls.extend(local_urls)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        price_container = soup.find('p', 'price')

        part_number_tag = soup.find(
            'div', 'woocommerce-product-details__short-description')

        if part_number_tag and part_number_tag.find('p'):
            part_number = part_number_tag.find('p').text.strip()[:40]
        else:
            part_number = None

        if price_container.find('ins'):
            price = Decimal(remove_words(price_container.find('ins').text))
        else:
            price = Decimal(remove_words(price_container.text))

        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]

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
            picture_urls=picture_urls,
            part_number=part_number
        )
        return [p]
