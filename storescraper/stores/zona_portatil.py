import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, TABLET, HEADPHONES, \
    VIDEO_GAME_CONSOLE, GAMING_CHAIR, KEYBOARD, COMPUTER_CASE, RAM, \
    MOTHERBOARD, PROCESSOR, VIDEO_CARD, STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, MEMORY_CARD, MONITOR, PRINTER, STEREO_SYSTEM, \
    MICROPHONE, CPU_COOLER, POWER_SUPPLY
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class ZonaPortatil(StoreWithUrlExtensions):
    url_extensions = [
        ['all-in-one-todo-en-uno', ALL_IN_ONE],
        ['notebook', NOTEBOOK],
        ['tablets', TABLET],
        ['audifonos-accesorios', HEADPHONES],
        ['parlantes', STEREO_SYSTEM],
        ['consolas', VIDEO_GAME_CONSOLE],
        ['sillas-gamer', GAMING_CHAIR],
        ['teclados-mouse', KEYBOARD],
        ['gabinetes', COMPUTER_CASE],
        ['memorias-notebook', RAM],
        ['memorias-pc', RAM],
        ['placas-madres', MOTHERBOARD],
        ['procesadores', PROCESSOR],
        ['tarjetas-graficas', VIDEO_CARD],
        ['discos-duros-pc', STORAGE_DRIVE],
        ['discos-duros-notebook', STORAGE_DRIVE],
        ['discos-ssd', SOLID_STATE_DRIVE],
        ['discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
        ['ssd-externos', EXTERNAL_STORAGE_DRIVE],
        ['discos-duros-video-vigilancia', STORAGE_DRIVE],
        ['memorias-flash', MEMORY_CARD],
        ['monitores', MONITOR],
        ['impresoras', PRINTER],
        ['fuente-de-poder', POWER_SUPPLY],
        ['monitores-zona-gamer', MONITOR],
        ['sillas-gamer', GAMING_CHAIR],
        ['gabinetes-zona-gamer', COMPUTER_CASE],
        ['audifonos', HEADPHONES],
        ['teclados-mouse-zona-gamer', KEYBOARD],
        ['microfonos', MICROPHONE],
        ['refrigeracion', CPU_COOLER],
        ['placas-madres-zona-gamer', MOTHERBOARD],
        ['procesadores-zona-gamer', PROCESSOR],
        ['tarjetas-graficas-zona-gamer', VIDEO_CARD],
        ['cyber-zona-portatil', MONITOR]
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)

            if 'cyber-zona-portatil' == url_extension:
                url_webpage = 'https://www.zonaportatil.cl/' \
                    'cyber-zona-portatil/'
            else:
                url_webpage = 'https://www.zonaportatil.cl/categoria-pro' \
                    'ducto/{}/page/{}/'.format(url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('li', 'product')

            if not product_containers:
                if page == 1:
                    logging.warning('Empty category')
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

            if 'cyber-zona-portatil' == url_extension:
                break
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text

        if soup.find('p', 'price').find('ins'):
            normal_price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price_text = soup.find('p', 'price').text.strip()
            if not price_text:
                return []
            normal_price = Decimal(remove_words(price_text))
        offer_price = (normal_price * Decimal('0.95')).quantize(0)

        if 'OPEN BOX' in name:
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'
        sku = soup.find('span', 'sku').text
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        picture_urls = ['https://www.zonaportatil.cl' + tag['src'] for tag in
                        soup.find('div', 'woocommerce-product-gallery')
                        .findAll('img')]
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
            condition=condition

        )
        return [p]
