import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class OrbitalStore(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'Ram',
            'Monitor',
            'Processor',
            'VideoCard',
            'Motherboard',
            CPU_COOLER,
            'Mouse',
            'Keyboard',
            # 'Headphones',
            'Notebook',
            # 'Printer'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://www.orbitalstore.mx/{}'

        url_extensions = [
            ['accesorios/disco-duro-externo.html', 'ExternalStorageDrive'],
            ['almacenamiento/hdd-pc.html', 'StorageDrive'],
            ['almacenamiento/ssd.html', 'SolidStateDrive'],
            ['desktop-pc/componentes/fuente-de-poder.html', 'PowerSupply'],
            ['desktop-pc/componentes/gabinetes-pc.html', 'ComputerCase'],
            ['desktop-pc/componentes/memoria-ram.html', 'Ram'],
            ['monitores.html', 'Monitor'],
            ['desktop-pc/componentes/procesadores.html', 'Processor'],
            ['desktop-pc/componentes/tarjetas-de-video.html', 'VideoCard'],
            ['desktop-pc/componentes/motherboards.html', 'Mogherboard'],
            ['desktop-pc/componentes/efriamiento-y-ventilacion.html',
             CPU_COOLER],
            ['perifericos/mouse.html', 'Mouse'],
            ['perifericos/teclados.html', 'Keyboard'],
            ['perifericos/audio/audifonos.html', 'Headphones'],
            ['laptop/equipos-de-linea.html', 'Notebook'],
            ['perifericos/impresion-y-escaners/impresion-laser.html',
             'Printer'],
            ['perifericos/impresion-y-escaners/'
             'impresion-inyeccion-de-tinta.html', 'Printer']
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            category_url = url_base.format(url_extension)
            page = 1
            done = False

            while True:
                if page >= 15:
                    raise Exception('Page overflow: ' + category_url)

                url = category_url + '?limit=30&p={}'.format(page)
                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                products = list(set(soup.findAll('h3', 'product-name')))

                if not products:
                    raise Exception('Empty category: ' + category_url)

                for product in products:
                    product_url = product.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break
                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('div', 'product-name').find('h1').text
        sku = soup.find(
            'div', 'product_info_left').find('p').find('b').text[:50]

        if soup.find('p', 'out-of-stock'):
            stock = 0
        else:
            stock = -1

        price = Decimal(
            soup.find('div', 'price-box').find('span', 'price')
                .text.replace('$', '').replace(',', ''))

        images_container = soup.find('ul', 'slides')

        if images_container:
            picture_urls = []

            for image in images_container.findAll('li'):
                picture_urls.append(image.find('a')['href'])
        else:
            picture_urls = None

        description = html_to_markdown(
            str(soup.find('div', 'short-description')))

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
            description=description
        )

        return [p]
