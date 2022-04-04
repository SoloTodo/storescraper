import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import PROCESSOR, MOTHERBOARD, RAM, \
    SOLID_STATE_DRIVE, VIDEO_CARD, COMPUTER_CASE, POWER_SUPPLY, CPU_COOLER, \
    MOUSE, HEADPHONES, MONITOR, GAMING_CHAIR, PRINTER, GAMING_DESK, CASE_FAN, \
    NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


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
            GAMING_DESK,
            CASE_FAN,
            NOTEBOOK,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['1', HEADPHONES],  # AUDIO
            ['6', MONITOR],  # MONITORES
            ['8', CPU_COOLER],  # REFRIGERACION
            ['9', MOUSE],  # TECLADOS/MOUSE
            ['10', MOTHERBOARD],  # PLACAS MADRE
            ['11', PROCESSOR],  # PROCESADORES
            ['12', RAM],  # MEMORIAS
            ['13', SOLID_STATE_DRIVE],  # DISCOS DUROS
            ['14', COMPUTER_CASE],  # GABINETES
            ['15', POWER_SUPPLY],  # FUENTES DE PODER
            ['16', VIDEO_CARD],  # TARJETAS DE VIDEO
            ['21', GAMING_CHAIR],  # SILLAS GAMER
            ['33', GAMING_DESK],  # ESCRITORIOS
            ['27', PRINTER],  # IMPRESORAS
            ['17', NOTEBOOK],  # Computadores
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            data = session.post(
                'https://tienda.pc-gamer.cl/php/traer_productos.php',
                data={'search_cat': url_extension}).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', 'product-wrapper')
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

        for row in soup.find('div', {'id': 'prices-product'}).find(
                'table', 'table').findAll('tr')[1:]:
            stock += int(row.findAll('td')[-1].text)

        normal_price = Decimal(
            soup.find('div', 'price-normal').find('h2').text.split()[1]
                .replace('.', ''))
        offer_price = Decimal(
            soup.find('div', 'price-oferta').find('h3').text.split()[1]
                .replace('.', ''))
        image = soup.find('div', 'single_product').findAll('img')[0]['src']
        picture_urls = [f'https://tienda.pc-gamer.cl/{image}']

        description = html_to_markdown(
            str(soup.find('div', {'id': 'product-description'})))

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
            description=description
        )

        return [p]
