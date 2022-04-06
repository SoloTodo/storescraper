import json
import logging

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, GAMING_DESK, MICROPHONE, \
    CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class NotebookStore(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Tablet',
            'Wearable',
            'Notebook',
            'AllInOne',
            'UsbFlashDrive',
            'MemoryCard',
            'Ram',
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'Processor',
            'VideoCard',
            'Motherboard',
            'ComputerCase',
            'Monitor',
            'Television',
            'StereoSystem',
            'Printer',
            'VideoGameConsole',
            'PowerSupply',
            CPU_COOLER,
            GAMING_CHAIR,
            GAMING_DESK,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Portabilidad
            ['tecnologia-portatil/celulares/'
             'celulares-desbloqueados.html', 'Cell'],
            ['tecnologia-portatil/celulares/tableta-2.html', 'Tablet'],
            ['tecnologia-portatil/relojes-y-trackers/'
             'trackers-de-actividad.html', 'Wearable'],
            # Equipos
            ['equipos/computadores-1/portatiles-1.html', 'Notebook'],
            ['equipos/computadores-1/ultrabooks.html', 'Notebook'],
            ['equipos/computadores-1/todo-en-uno.html', 'AllInOne'],
            ['equipos/memorias/unidades-flash-usb.html', 'UsbFlashDrive'],
            ['equipos/memorias/tarjetas-de-memoria-flash.html', 'MemoryCard'],
            ['equipos/memorias/modulos-ram-genericos.html', 'Ram'],
            ['equipos/memorias/memoria-ram.html', 'Ram'],
            ['equipos/alm/discos-duros-externos.html', 'ExternalStorageDrive'],
            ['equipos/alm/discos-duros-internos.html', 'StorageDrive'],
            ['equipos/alm/discos-de-estado-solido.html', 'SolidStateDrive'],
            ['equipos/perifericos/ratones.html', 'Mouse'],
            ['equipos/perifericos/'
             'teclados-y-teclados-de-numeros.html', 'Keyboard'],
            ['equipos/perifericos/'
             'combos-de-teclado-y-raton.html', 'KeyboardMouseCombo'],
            ['equipos/perifericos/'
             'auriculares-y-manos-libres.html', 'Headphones'],
            ['equipos/componentes-informaticos/procesadores.html',
             'Processor'],
            ['equipos/componentes-informaticos/tarjetas-de-video.html',
             'VideoCard'],
            ['equipos/componentes-informaticos/tarjetas-madre-'
             'placas-madre.html', 'Motherboard'],
            ['equipos/componentes-informaticos/fuentes-de-poder.html',
             'PowerSupply'],
            ['equipos/componentes-informaticos/cajas-gabinetes.html',
             'ComputerCase'],
            ['equipos/componentes-informaticos/ventiladores-y-sistemas'
             '-de-enfriamiento.html', CPU_COOLER],
            # Audio Video y Foto
            ['audio-y-video/monitores-proyectores/monitores.html', 'Monitor'],
            ['audio-y-video/monitores-proyectores/'
             'televisores.html', 'Television'],
            ['audio-y-video/audio-y-video/auriculares.html', 'Headphones'],
            ['audio-y-video/audio-y-video/'
             'parlantes-bocinas-cornetas-1.html', 'StereoSystem'],
            # Impresion
            ['impresion/impresoras-y-escaneres.html', 'Printer'],
            # Gaming
            ['gaming/equipos/notebooks.html', 'Notebook'],
            ['gaming/equipos/monitores.html', 'Monitor'],
            ['gaming/accesorios/audifonos.html', 'Headphones'],
            ['gaming/accesorios/teclados-y-mouse.html', 'Mouse'],
            ['gaming/componentes/fuentes-de-poder.html', 'PowerSupply'],
            ['gaming/componentes/tarjetas-madre.html', 'Motherboard'],
            ['gaming/componentes/gabinetes.html', 'ComputerCase'],
            ['gaming/componentes/enfriamiento.html', CPU_COOLER],
            ['gaming/componentes/memoria-ram.html', 'Ram'],
            ['gaming/componentes/procesadores.html', 'Processor'],
            ['gaming/accesorios/sillas.html', GAMING_CHAIR],
            ['equipos/muebles/escritorios.html', GAMING_DESK],
            ['audio-y-video/audio-y-video/microfonos.html', MICROPHONE]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page > 15:
                    raise Exception('Page overflow')

                url = 'https://notebookstore.cl/{}?p={}'.format(
                    category_path, page)
                print(url)

                soup = BeautifulSoup(session.get(url).text, 'html5lib')
                products = soup.findAll('li', 'product')

                if not products:
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

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('span', {'itemprop': 'name'}).text
        sku = soup.find('div', {'itemprop': 'sku'}).text

        stock = 0
        stock_container = soup.find('div', 'product-stock')

        if stock_container:
            stock = int(stock_container.text.strip().split(' ')[1])

        offer_price = Decimal(soup.find('span', 'efectivo').find(
            'span', 'price').text.replace('$', '').replace('.', '')
            ).quantize(Decimal('1.'))
        normal_price = (offer_price * Decimal(1.034)
                        ).quantize(Decimal('1.'))

        image_scripts = soup.findAll('script', {'type': 'text/x-magento-init'})
        picture_urls = []

        for script in image_scripts:
            if 'mage/gallery/gallery' in script.text:
                image_data = json.loads(script.text)[
                    '[data-gallery-role=gallery-placeholder]'][
                    'mage/gallery/gallery']['data']
                for data in image_data:
                    picture_urls.append(data['img'])

        description = html_to_markdown(
            str(soup.find('div', 'description')))

        if len(sku) > 50:
            sku = sku[0:50]

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
