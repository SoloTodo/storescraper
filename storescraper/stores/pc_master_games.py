import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, SOLID_STATE_DRIVE, NOTEBOOK, \
    RAM, POWER_SUPPLY, COMPUTER_CASE, MONITOR, GAMING_CHAIR, \
    WEARABLE, HEADPHONES, MOUSE, KEYBOARD, PROCESSOR
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
            PROCESSOR
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
            ['disco-ssd', SOLID_STATE_DRIVE],
            ['equipos', NOTEBOOK],
            ['memoria-ram', RAM],
            ['sillas-gamer', GAMING_CHAIR],
            ['smartwatch', WEARABLE],
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
                url_webpage = 'https://pcmastergames.cl/{}/page/{}/' \
                    .format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'products')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll(
                        'div', 'product-grid-item'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if not soup.find('p', 'stock'):
            stock = -1
        elif soup.find('p', 'stock').text == 'Agotado':
            stock = 0
        else:
            stock = int(soup.find('p', 'stock').text.split()[0])
        if soup.find('p', 'price').text == '':
            return []
        elif soup.find('p', 'price').find('ins'):
            price = Decimal(remove_words(soup.find('p').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p').text))
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

        )

        return [p]
