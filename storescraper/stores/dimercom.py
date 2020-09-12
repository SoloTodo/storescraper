import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, \
    html_to_markdown
from storescraper.categories import STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    MOTHERBOARD, PROCESSOR, RAM, VIDEO_CARD, POWER_SUPPLY, COMPUTER_CASE, \
    MOUSE, KEYBOARD, MONITOR, TABLET


class Dimercom(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            MOTHERBOARD,
            PROCESSOR,
            RAM,
            VIDEO_CARD,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOUSE,
            KEYBOARD,
            MONITOR,
            TABLET,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Don't use extensions without underscore ("_") because Dimercom
        # main categories don't list all of the products of the subcategories
        url_extensions = [
            # Discos duros internos
            ['6_109', STORAGE_DRIVE],
            # Unidades SSD
            ['6_110', SOLID_STATE_DRIVE],
            # Tarjetas madre AMD
            ['27_255', MOTHERBOARD],
            # Tarjetas madre Gamer
            ['27_256', MOTHERBOARD],
            # Tarjetas madre Intel
            ['27_257', MOTHERBOARD],
            # Procesadores A-Series
            ['17_175', PROCESSOR],
            # Procesadores AMD
            ['7_176', PROCESSOR],
            # Procesadores Celeron
            ['17_177', PROCESSOR],
            # Procesadores Core
            ['17_178', PROCESSOR],
            # Procesadores Intel
            ['17_180', PROCESSOR],
            # Procesadores Pentium
            ['17_181', PROCESSOR],
            # Procesadores Ryzen
            ['17_182', PROCESSOR],
            # Procesadores Xeon
            ['17_183', PROCESSOR],
            # Memorias RAM para Desktop
            ['13_138', RAM],
            # Memorias RAM para Laptop
            ['13_139', RAM],
            # Tarjetas de video NVIDIA
            ['26_253', VIDEO_CARD],
            # Tarjetas de video Radeon
            ['26_254', VIDEO_CARD],
            # Fuentes de Poder
            ['9_116', POWER_SUPPLY],
            # Gabinetes
            ['10_123', COMPUTER_CASE],
            # Teclados
            ['1_64', KEYBOARD],
            # Mouse
            ['1_56', MOUSE],
            # Monitores 15.6"
            ['14_143', MONITOR],
            # Monitores 18.5"
            ['14_144', MONITOR],
            # Monitores 19.5"
            ['14_145', MONITOR],
            # Monitores 20"
            ['14_146', MONITOR],
            # Monitores 21.5"
            ['14_147', MONITOR],
            # Monitores 23"
            ['14_148', MONITOR],
            # Monitores 23.5"
            ['14_149', MONITOR],
            # Monitores 23.6"
            ['14_150', MONITOR],
            # Monitores 23.8"
            ['14_151', MONITOR],
            # Monitores 24"
            ['14_152', MONITOR],
            # Monitores 25"
            ['14_153', MONITOR],
            # Monitores 27"
            ['14_154', MONITOR],
            # Monitores 28"
            ['14_155', MONITOR],
            # Monitores 29"
            ['14_156', MONITOR],
            # Monitores 31.5"
            ['14_157', MONITOR],
            # Monitores 32"
            ['14_158', MONITOR],
            # Monitores 34"
            ['14_159', MONITOR],
            # Monitores LED
            ['14_160', MONITOR],
            # Tablets
            ['25_250', TABLET],
        ]

        base_url = 'https://www.dimercom.mx/index.php?' \
                   'route=product/category&path={}&page={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)
                print(url)

                if page > 20:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_container = soup.find('div', 'product-list')

                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                products = product_container.findAll('div', 'image')

                for product in products:
                    if product.find('a'):
                        product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html5lib')

        name = soup.find('div', 'right').find('h1').text
        sku = soup.find('input', {'name': 'product_id'})['value']

        description_data = soup.find('div', 'description').findAll('span')

        stock = 0

        for data in description_data:
            split_data = data.text.split(':')
            if len(split_data) > 1:
                if "Disponible" in split_data[0]:
                    stock = int(split_data[1])

        if not stock:
            if 'Disponible' in soup.find('div', 'description').text:
                stock = -1

        price = Decimal(
            soup.find('span', 'price-fixed').text
                .replace('$', '').replace(',', ''))

        picture_urls = [
            soup.find('a', 'jqzoom colorbox')['href'].replace(' ', '%20')]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

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
            'MXN',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
