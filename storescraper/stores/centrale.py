import json
import logging
from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, \
    EXTERNAL_STORAGE_DRIVE, POWER_SUPPLY, RAM, \
    MOTHERBOARD, PROCESSOR, VIDEO_CARD, NOTEBOOK, TABLET, \
    MONITOR, PRINTER, UPS, MOUSE, COMPUTER_CASE, HEADPHONES, STEREO_SYSTEM, \
    ALL_IN_ONE, VIDEO_GAME_CONSOLE, CELL, WEARABLE, TELEVISION, GAMING_CHAIR, \
    KEYBOARD, CPU_COOLER, MICROPHONE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class Centrale(StoreWithUrlExtensions):
    url_extensions = [
        ['audifonos', HEADPHONES],
        ['sistemas-de-audio', STEREO_SYSTEM],
        ['all-in-one', ALL_IN_ONE],
        ['almacenamiento-externo', EXTERNAL_STORAGE_DRIVE],
        ['kits-teclados-y-mouses', MOUSE],
        ['mouses', MOUSE],
        ['notebooks', NOTEBOOK],
        ['tablets', TABLET],
        ['teclados', KEYBOARD],
        ['ups-y-reguladores', UPS],
        ['smartwatches-electro', WEARABLE],
        ['televisores', TELEVISION],
        ['consolas', VIDEO_GAME_CONSOLE],
        ['impresoras', PRINTER],
        ['plotters', PRINTER],
        ['monitores', MONITOR],
        ['sillas-muebles-y-sillas', GAMING_CHAIR],
        ['plotters', PRINTER],
        ['almacenamiento', SOLID_STATE_DRIVE],
        ['fuentes-de-poder', POWER_SUPPLY],
        ['gabinetes-desktop', COMPUTER_CASE],
        ['memorias-ram', RAM],
        ['placas-madres', MOTHERBOARD],
        ['procesadores-pc', PROCESSOR],
        ['refrigeración', CPU_COOLER],
        ['tarjetas-de-video', VIDEO_CARD],
        ['smartphones', CELL],
        ['micrófono', MICROPHONE]
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 20:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://centrale.cl/categoria-producto' \
                          '/{}/page/{}'.format(url_extension, page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', 'product-small box')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category; ' + url_webpage)
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

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)

        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        modified_notebook_parts_label = soup.find('strong', text='COMPONENTES')
        if modified_notebook_parts_label:
            part_number_components = []
            table_tag = modified_notebook_parts_label.parent.find('table')
            for row in table_tag.findAll('tr')[1:]:
                component_mpn = row.findAll('td')[1].text
                part_number_components.append(component_mpn)
            part_number = ' + '.join(part_number_components)
        else:
            part_number = product_data['mpn'] or None

        name = product_data['name'].strip()
        sku = product_data['sku'].strip()
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        offer_price = Decimal(remove_words(
            soup.find(
                'div', {'style': 'margin-bottom: -4px;'}).text.split('$')[1]))
        normal_price = Decimal(remove_words(soup.find('span', {
            'style': 'font-size: 23px; '
                     'font-weight: bold; color: black;'}).text.split()[0]))
        picture_urls = []
        picture_container = soup.find('div', 'product-thumbnails')
        if picture_container:
            for tag in picture_container.findAll(
                    'img', 'attachment-woocommerce_thumbnail'):
                picture_urls.append(
                    tag['src'].replace('-300x300', ''))
        elif soup.find('div', 'woocommerce-product-gallery__image'):
            picture_urls.append(
                soup.find('div', 'woocommerce-product-gallery__image').find(
                    'img')['src'])

        picture_urls = [x for x in picture_urls if validators.url(x)]

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
            part_number=part_number
        )
        return [p]
