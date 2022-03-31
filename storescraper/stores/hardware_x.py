import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, PROCESSOR, MOTHERBOARD, RAM, \
    SOLID_STATE_DRIVE, MOUSE, KEYBOARD, MONITOR, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class HardwareX(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            PROCESSOR,
            MOTHERBOARD,
            RAM,
            SOLID_STATE_DRIVE,
            MOUSE,
            KEYBOARD,
            MONITOR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes-pc/procesadores', PROCESSOR],
            ['componentes-pc/placas-madres', MOTHERBOARD],
            ['componentes-pc/memorias-ram', RAM],
            ['componentes-pc/almacenamiento', SOLID_STATE_DRIVE],
            ['perifericos/monitores', MONITOR],
            ['perifericos/teclados', KEYBOARD],
            ['perifericos/mouse', MOUSE],
            ['perifericos/audifonos', HEADPHONES]
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
                url_webpage = 'https://www.hardwarex.cl/wp/categoria-pro' \
                    'ducto/{}/page/{}/'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
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

        key = soup.find('link', {'rel': 'shortlink'})[
            'href'].split('=')[-1]

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[1].text)

        name = json_data['name']
        sku = str(json_data['sku'])[50:]
        price = Decimal(json_data['offers'][0]['price'])

        max_input = soup.find('input', 'input-text qty text')
        if max_input:
            stock = int(max_input['max'])
        else:
            stock = 0

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        pictures_urls = []
        image_containers = soup.find('div', 'wpgs-for')
        for i in image_containers.findAll('img'):
            pictures_urls.append(i['src'])

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
            picture_urls=pictures_urls,
            description=description
        )
        return [p]
