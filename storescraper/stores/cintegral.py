import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Cintegral(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Tablet',
            'StorageDrive',
            'PowerSupply',
            'ComputerCase',
            'Ram',
            'Monitor',
            'Processor',
            'VideoCard',
            'Motherboard',
            'Printer',
            'Cell',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'AllInOne',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://www.cintegral.cl/'

        url_extensions = [
            ['pc-y-portatiles/portatiles/notebook.html', 'Notebook'],
            ['pc-y-portatiles/portatiles/tablet.html', 'Tablet'],
            ['pc-y-portatiles/partes-y-piezas/cpu.html', 'Processor'],
            ['pc-y-portatiles/partes-y-piezas/almacenamiento/'
             'discos-duros-pc.html', 'StorageDrive'],
            ['pc-y-portatiles/partes-y-piezas/almacenamiento/'
             'discos-duros-externos.html', 'ExternalStorageDrive'],
            ['pc-y-portatiles/partes-y-piezas/almacenamiento/ssd.html',
             'SolidStateDrive'],
            ['pc-y-portatiles/partes-y-piezas/almacenamiento/'
             'memorias-flash.html', 'MemoryCard'],
            ['pc-y-portatiles/partes-y-piezas/almacenamiento/pendrive.html',
             'UsbFlashDrive'],
            ['pc-y-portatiles/partes-y-piezas/gabinetes.html', 'ComputerCase'],
            ['pc-y-portatiles/partes-y-piezas/fuentes-de-poder.html',
             'PowerSupply'],
            ['pc-y-portatiles/partes-y-piezas/placa-madre.html',
             'Motherboard'],
            ['pc-y-portatiles/partes-y-piezas/memorias.html', 'Ram'],
            ['pc-y-portatiles/partes-y-piezas/tarjetas-de-video.html',
             'VideoCard'],
            ['impresion-e-imagen/impresoras-de-tinta.html', 'Printer'],
            ['impresion-e-imagen/impresoras-laser.html', 'Printer'],
            ['impresion-e-imagen/multifuncionales.html', 'Printer'],
            ['impresion-e-imagen/multifuncionales-laser.html', 'Printer'],
            ['monitores-y-proyeccion/monitores.html', 'Monitor'],
            ['pc-y-portatiles/mouse-teclados/mouse.html', 'Mouse'],
            ['pc-y-portatiles/mouse-teclados/teclados.html', 'Keyboard'],
            ['pc-y-portatiles/mouse-teclados/combo-mouse-teclado.html',
             'KeyboardMouseCombo'],
            ['audio/audifonos.html', 'Headphones'],
            ['pc-y-portatiles/escritorio/todo-en-uno-aio.html', 'AllInOne'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['X-Requested-With'] = 'XMLHttpRequest'

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            category_url = url_base + 'index.php/' + url_extension
            page = 1

            local_product_urls = []

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                url = category_url + '?p=' + str(page)
                print(url)
                json_data = json.loads(session.get(url, verify=False).text)
                soup = BeautifulSoup(json_data['listing'], 'html.parser')

                done = False

                containers = soup.findAll('a', 'product-image')

                if not containers:
                    raise Exception('Empty category: ' + category_url)

                for product_link in containers:
                    product_url = product_link['href']
                    if product_url in local_product_urls:
                        done = True
                        break
                    local_product_urls.append(product_url)
                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url, verify=False).text
        soup = BeautifulSoup(page_source, 'html.parser')
        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('li', 'product').find('strong').text.split(
            ':')[1].strip()
        part_number = re.search(
            r"ccs_cc_args.push\(\['pn', '(.*)'\]\);", page_source).groups()[0]
        if not part_number:
            part_number = None

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

        if soup.find('button', {'id': 'product-addtocart-button'}):
            stock = -1
        else:
            stock = 0

        price_box = soup.find('div', 'price-box')
        special_price_container = price_box.find('p', 'special-price')
        if special_price_container:
            price = Decimal(remove_words(special_price_container.find(
                'span', 'price').text.strip()))
        else:
            price = Decimal(remove_words(price_box.find(
                'span', 'regular-price').find('span', 'price').text.strip()))

        picture_urls = [link['href'] for link in soup.findAll('a', 'lightbox')]

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
