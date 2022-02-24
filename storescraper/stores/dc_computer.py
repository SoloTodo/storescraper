import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR, KEYBOARD, MOUSE, HEADPHONES, \
    COMPUTER_CASE, GAMING_CHAIR, POWER_SUPPLY, RAM, PROCESSOR, MOTHERBOARD, \
    CPU_COOLER, VIDEO_CARD, SOLID_STATE_DRIVE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class DcComputer(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            MOUSE,
            KEYBOARD,
            HEADPHONES,
            COMPUTER_CASE,
            GAMING_CHAIR,
            POWER_SUPPLY,
            RAM,
            PROCESSOR,
            MOTHERBOARD,
            CPU_COOLER,
            VIDEO_CARD,
            SOLID_STATE_DRIVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['monitores', MONITOR],
            ['perifericos/mouse', MOUSE],
            ['perifericos/teclados', KEYBOARD],
            ['audifonos', HEADPHONES],
            ['gabinetes', COMPUTER_CASE],
            ['sillas-gamer', GAMING_CHAIR],
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/memorias-ram', RAM],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/placas-madres', MOTHERBOARD],
            ['componentes/refrigeracion', CPU_COOLER],
            ['componentes/tarjeta-de-video', VIDEO_CARD],
            ['componentes/unidad-de-estado-solido-ssd', SOLID_STATE_DRIVE],
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

                url_webpage = 'https://dccomputer.cl/categoria-producto/' \
                              '{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('empty category' + url_extension)
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
        name = soup.find('h1', 'product_title').text
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        sku_tag = soup.find('span', 'sku')

        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None

        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        else:
            stock = int(soup.find('p', 'stock').text.split()[0])

        offer_price = Decimal(remove_words(soup.find('p', 'price').findAll(
            'bdi')[-1].text))
        normal_price = (offer_price * Decimal('1.04')).quantize(0)
        picture_urls = [tag['src'] for tag in soup.find('div', 'woocommerce'
                        '-product-gallery').findAll('img')]
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
            part_number=sku
        )
        return [p]
