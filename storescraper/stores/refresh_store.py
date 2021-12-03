import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import KEYBOARD, MOUSE, HEADPHONES, \
    SOLID_STATE_DRIVE, STORAGE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, RAM, \
    MONITOR, MOTHERBOARD, PROCESSOR, CPU_COOLER, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words
from urllib.parse import quote


class RefreshStore(Store):
    @classmethod
    def categories(cls):
        return [
            KEYBOARD,
            MOUSE,
            HEADPHONES,
            SOLID_STATE_DRIVE,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            VIDEO_CARD
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios?byType=13', KEYBOARD],
            ['accesorios?byType=14', MOUSE],
            ['accesorios?byType=21', HEADPHONES],
            ['almacenamiento?byType=18', SOLID_STATE_DRIVE],
            ['almacenamiento?byType=20', SOLID_STATE_DRIVE],
            ['almacenamiento?byType=19', STORAGE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['ram', RAM],
            ['monitores', MONITOR],
            ['placas-madres', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['Cooler-Cpu', CPU_COOLER],
            ['tarjetas-de-video', VIDEO_CARD]
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

                if '?' in url_extension:
                    separator = '&'
                else:
                    separator = '?'

                url_webpage = 'https://refreshstore.cl/{}{}sort=alf1' \
                              '&page={}'.format(url_extension, separator, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('div', 'contenedorImagen')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_sku = re.search(
                        r"verProducto\('(.+)'\)",
                        container.find('img')['onclick']).groups()[0]
                    product_url = 'https://www.refreshstore.cl/producto/' + \
                                  product_sku
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1').text
        canonical_url = soup.find('link', {'rel': 'canonical'})['href']
        sku = canonical_url.split('/')[-1].strip()
        bodega_ids = ['bodegastock1', 'bodegastock2']

        for bodega_id in bodega_ids:
            bodega_tag = soup.find('h6', {'id': bodega_id})
            if bodega_tag and bodega_tag.text.strip() == 'Disponible':
                stock = -1
                break
        else:
            stock = 0

        offer_price = Decimal(remove_words(
            soup.find('meta', {'name': 'description'})['content'].split()[1]))
        normal_price = Decimal(remove_words(
            soup.find('h2', {'style': 'color: #00cbcd;'}).text))
        picture_urls = [quote(tag['src'], safe='/:') for tag in
                        soup.find('div', 'carousel slide').findAll('img')]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,

        )
        return [p]
