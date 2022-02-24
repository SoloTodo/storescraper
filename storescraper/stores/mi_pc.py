import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class MiPc(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            CPU_COOLER,
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Monitor',
            'Tablet',
            'Notebook',
            'Cell',
            'Television',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['hardware/almacenamiento-interno/disco-duro.html',
             'StorageDrive'],
            ['gamer/almacenamiento-interno/disco-duro.html',
             'StorageDrive'],
            ['hardware/almacenamiento-interno/ssd.html', 'SolidStateDrive'],
            ['gamer/almacenamiento-interno/ssd.html', 'SolidStateDrive'],
            ['hardware/tarjetas-madre.html', 'Motherboard'],
            ['gamer/tarjetas-madre.html', 'Motherboard'],
            ['hardware/procesadores.html', 'Processor'],
            ['gamer/procesadores.html', 'Processor'],
            ['hardware/enfriamiento/disipador-cpu.html', CPU_COOLER],
            ['gamer/enfriamiento/liquido.html', CPU_COOLER],
            ['hardware/ram.html', 'Ram'],
            ['gamer/ram.html', 'Ram'],
            ['hardware/tarjeta-de-video.html', 'VideoCard'],
            ['gamer/tarjeta-de-video.html', 'VideoCard'],
            ['hardware/fuentes-de-poder.html', 'PowerSupply'],
            ['gamer/fuentes-de-poder.html', 'PowerSupply'],
            ['hardware/gabinetes.html', 'ComputerCase'],
            ['gamer/gabinetes.html', 'ComputerCase'],
            ['gamer/mouse-y-teclado/mouse.html', 'Mouse'],
            ['gamer/mouse-y-teclado/mouse-usb.html', 'Mouse'],
            ['gamer/mouse-y-teclado/teclado.html', 'Keyboard'],
            ['gamer/mouse-y-teclado/teclado-usb.html', 'Keyboard'],
            ['gamer/mouse-y-teclado/kit.html', 'KeyboardMouseCombo'],
            ['hardware/monitores.html', 'Monitor'],
            ['gamer/monitores.html', 'Monitor'],
            ['equipos/tablets.html', 'Tablet'],
            ['gamer/laptop.html', 'Notebook'],
            ['equipos/laptop.html', 'Notebook'],
            ['audio-y-video/pantallas/tv.html', 'Television'],
        ]

        base_url = 'https://mipc.com.mx/{}'

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                url = base_url.format(url_extension)

                if page > 1:
                    url += '?p={}'.format(page)

                print(url)

                if page >= 20:
                    raise Exception('Page overflow: ' + url)

                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                products = soup.findAll('li', 'product')

                if not products:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                for product in products:
                    product_url = product.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        response = session.get(url)

        if response.status_code in [404]:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html5lib')

        name = soup.find('h1', 'name').text
        sku = soup.find('div', {'itemprop': 'sku'}).text

        availability = soup.find('div', 'availability')

        if availability:
            stock = int(soup.find('div', 'availability').find('strong').text)
        else:
            stock = 0

        price = Decimal(
            soup.find('span', 'price').text
                .replace('$', '').replace(',', ''))

        if soup.find('div', {'id': 'owl-carousel-gallery'}):
            picture_urls = [i['src'] for i in soup.find(
                'div', {'id': 'owl-carousel-gallery'})
                .findAll('img', 'img-fluid')]
        else:
            picture_urls = [soup.find('img', 'img-fluid')['src']]

        description = html_to_markdown(
            str(soup.find('div', 'description')))

        ths = soup.findAll('th')
        part_number = None

        for th in ths:
            if th.text == "mpn":
                part_number = th.parent.find('td').text

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
            part_number=part_number
        )

        return [p]
