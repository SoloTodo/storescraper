import json
import random

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class PcOfertas(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'VideoCard',
            'Processor',
            'Monitor',
            'Television',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'PowerSupply',
            'ComputerCase',
            'Tablet',
            'Printer',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # ['computadores-notebooks-y-tablets/moviles/notebooks.html',
            #  'Notebook'],
            # ['computadores-notebooks-y-tablets/moviles/ultrabooks.html',
            #  'Notebook'],
            # ['computadores-notebooks-y-tablets/moviles/equipos-2-en-1.html',
            #  'Notebook'],
            # ['apple/mac/macbook.html', 'Notebook'],
            # ['apple/mac/macbook-air.html', 'Notebook'],
            # ['apple/mac/macbook-pro.html', 'Notebook'],
            # ['apple/mac/macbook-pro-retina.html', 'Notebook'],
            ['partes-y-piezas/display/tarjetas-de-video.html', 'VideoCard'],
            ['partes-y-piezas/componentes/cpu-procesadores.html',
             'Processor'],
            ['partes-y-piezas/display/monitores.html', 'Monitor'],
            ['partes-y-piezas/componentes/placas-madre.html', 'Motherboard'],
            ['partes-y-piezas/componentes/memorias/memorias.html', 'Ram'],
            ['partes-y-piezas/componentes/memorias/'
             'memorias-p-pc-escritorio.html', 'Ram'],
            ['partes-y-piezas/almacenamiento/discos-internos.html',
             'StorageDrive'],
            ['partes-y-piezas/almacenamiento/discos-de-estado-solido-ssd.html',
             'SolidStateDrive'],
            ['partes-y-piezas/componentes/fuentes-de-poder/'
             'fuentes-de-poder.html', 'PowerSupply'],
            # ['partes-y-piezas/componentes/gabinetes.html', 'ComputerCase'],
            # ['partes-y-piezas/display/televisores.html', 'Television'],
            # ['computadores-notebooks-y-tablets/moviles/tablets.html',
            #  'Tablet'],
            # ['apple/ipad.html', 'Tablet'],
            ['partes-y-piezas/impresoras/inyeccion-de-tinta.html', 'Printer'],
            ['partes-y-piezas/impresoras/http-laserwaca-com.html', 'Printer'],
            ['partes-y-piezas/almacenamiento/externos.html',
             'ExternalStorageDrive'],
            # ['accesorios-y-perifericos/perifericos/mouse/mouse.html',
            # 'Mouse'],
            # ['accesorios-y-perifericos/perifericos/teclados.html',
            # 'Keyboard'],
            # ['audiovisual/audio/audifonos.html', 'Headphones'],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        for url_extension, local_category in category_paths:
            if local_category != category:
                continue

            url = 'https://www.pcofertas.cl/' + url_extension
            p = 1

            local_product_urls = []

            while True:
                if p > 30:
                    raise Exception('Page overflow: ' + url)

                category_url = '{}?product_list_limit=40&p={}&_={}'.format(
                    url, p, random.randint(1, 1000))
                print(category_url)
                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                for cell in soup.find(
                        'ol', 'product-items').findAll('li', 'product-item'):
                    product_id_container = json.loads(
                        cell.find('a', 'towishlist')['data-post'])
                    product_id = product_id_container['data']['product']

                    product_url = 'https://www.pcofertas.cl/catalog/product/' \
                                  'view/id/' + product_id
                    local_product_urls.append(product_url)

                pager = soup.find('div', 'pages')
                if not pager or not pager.find('a', 'next'):
                    if not local_product_urls:
                        raise Exception('Empty category:' + category_url)
                    break

                p += 1

            product_urls.extend(local_product_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        request_url = '{}?_={}'.format(url, random.randint(1, 1000))
        response = session.get(request_url)

        if response.status_code == 404:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('span', {'itemprop': 'name'}).text.strip()
        part_number = soup.find('div', {'itemprop': 'sku'}).text.strip()
        sku = soup.find('div', 'price-final_price')['data-product-id'].strip()

        if soup.find('button', {'id': 'product-addtocart-button'}):
            stock = -1
        else:
            stock = 0

        price_containers = soup.findAll('span', 'price')

        price = Decimal(remove_words(price_containers[0].string))

        description = html_to_markdown(
            str(soup.find('div', {'id': 'product.info.description'})))

        picture_urls = [tag['data-image'] for tag in soup.findAll(
            'a', 'mt-thumb-switcher') if tag.get('data-image')]

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
