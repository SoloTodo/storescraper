import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import PROCESSOR, MOTHERBOARD, RAM, \
    SOLID_STATE_DRIVE, VIDEO_CARD, COMPUTER_CASE, POWER_SUPPLY, CPU_COOLER, \
    MOUSE, HEADPHONES, MONITOR, GAMING_CHAIR, PRINTER, GAMING_DESK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class PcGamer(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            COMPUTER_CASE,
            POWER_SUPPLY,
            CPU_COOLER,
            MOUSE,
            HEADPHONES,
            MONITOR,
            GAMING_CHAIR,
            PRINTER,
            GAMING_DESK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['11', PROCESSOR],  # Procesadores
            ['10', MOTHERBOARD],  # MB
            ['12', RAM],  # RAM Notebook
            ['13', SOLID_STATE_DRIVE],  # Almacenamiento
            ['16', VIDEO_CARD],  # Tarjetas de video
            ['14', COMPUTER_CASE],  # Gabinetes s/fuente
            ['15', POWER_SUPPLY],  # Fuentes de poder
            ['8', CPU_COOLER],  # Refrigeracion
            ['9', MOUSE],  # Mouse y teclados
            ['1', HEADPHONES],  # Audio
            ['6', MONITOR],  # Monitores
            ['21', GAMING_CHAIR],  # Sillas gamer
            ['27', PRINTER],  # Impresoras
            ['33', GAMING_DESK]  # Escritorio
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://tienda.pc-gamer.cl/categories.php?' \
                          'search_cat={}'.format(url_extension)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', 'product_item')
            if not product_containers:
                logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(
                    'https://tienda.pc-gamer.cl/' + product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('div', 'product_name').text
        sku = url.split('?id=')[1]

        stock = 0

        for row in soup.find('div', 'product_description').find(
                'table', 'table').findAll('tr')[1:]:
            stock += int(row.findAll('td')[-1].text)

        normal_price = Decimal(
            soup.find('div', 'price-normal').find('h3').text.split()[1]
                .replace('.', ''))
        offer_price = Decimal(
            soup.find('div', 'price-oferta').find('h2').text.split()[1]
                .replace('.', ''))
        picture_urls = []
        for tag in soup.find('ul', 'image_list').findAll('img'):
            if 'sinimagen' in tag['src']:
                continue
            picture_urls.append('https://tienda.pc-gamer.cl/' + tag['src'])

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
            picture_urls=picture_urls
        )

        return [p]
