import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown
from storescraper.categories import PROCESSOR, MOTHERBOARD, VIDEO_CARD, \
    POWER_SUPPLY, SOLID_STATE_DRIVE, MOUSE, COMPUTER_CASE, RAM, CPU_COOLER, \
    NOTEBOOK, STORAGE_DRIVE, EXTERNAL_STORAGE_DRIVE, MEMORY_CARD, \
    USB_FLASH_DRIVE, PRINTER, MONITOR


class Alfaomega(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            MOTHERBOARD,
            VIDEO_CARD,
            POWER_SUPPLY,
            SOLID_STATE_DRIVE,
            MOUSE,
            COMPUTER_CASE,
            RAM,
            CPU_COOLER,
            NOTEBOOK,
            STORAGE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            PRINTER,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['componentes-partes-y-piezas/procesador', PROCESSOR],
            ['componentes-partes-y-piezas/placas-madres', MOTHERBOARD],
            ['disco-de-estado-solido', SOLID_STATE_DRIVE],
            ['componentes-partes-y-piezas/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['componentes-partes-y-piezas/memorias', RAM],
            ['componentes-partes-y-piezas/'
             'mouse-y-teclados-componentes-partes-y-piezas', MOUSE],
            ['componentes-partes-y-piezas/refrigeracion', CPU_COOLER],
            ['componentes-partes-y-piezas/tarjetas-graficas', VIDEO_CARD],
            ['computadores-y-tables/mouse-y-teclados', MOUSE],
            ['computadores-y-tables/notebooks', NOTEBOOK],
            ['disco-duro', STORAGE_DRIVE],
            ['discos-duros-almacenamiento/disco-duros-para-pc', STORAGE_DRIVE],
            ['discos-duros-almacenamiento/discos-video-vigilancia',
             STORAGE_DRIVE],
            ['discos-duros-almacenamiento/discos-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['discos-duros-almacenamiento/discos-ssd', SOLID_STATE_DRIVE],
            ['discos-duros-almacenamiento/memorias-micro-sd', MEMORY_CARD],
            ['discos-duros-almacenamiento/pendrive', USB_FLASH_DRIVE],
            ['fuente-de-poder', POWER_SUPPLY],
            ['gabinetes-2', COMPUTER_CASE],
            ['impresora-hogar-y-oficina', PRINTER],
            ['impresoras-y-suministros', PRINTER],
            ['memorias-2', RAM],
            ['monitores-y-proyectores/monitores', MONITOR],
            ['mouse-y-teclados-2', MOUSE],
            ['tarjeta-de-video', VIDEO_CARD],
            ['placa-madre', MOTHERBOARD],
            ['placas-am4', MOTHERBOARD],
            ['placas-intel', MOTHERBOARD],
            ['procesador-2', PROCESSOR],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                url = 'https://aopc.cl/categoria/{}/page/{}'\
                    .format(category_path, page)
                print(url)
                response = session.get(url)

                if response.status_code == 404:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                products = soup.findAll('li', 'product-col')

                if not products:
                    break

                for product in products:
                    product_url = product.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        json_container = \
            json.loads(soup.find(
                'script', {'type': 'application/ld+json'}).text)

        name = json_container['name']
        sku = json_container['sku']
        stock_container = soup.find('span', 'stock')

        if stock_container:
            stock_text = stock_container.text.strip()
            stock = 0
            if stock_text != 'Agotado' and \
                    stock_text != 'Disponible para reserva':
                stock = int(stock_text.split(' ')[0])
        else:
            stock = -1

        offer_price = Decimal(json_container['offers'][0]['price'])
        normal_price = (offer_price * Decimal('1.05')).quantize(0)

        picture_containers = soup.findAll('div', 'img-thumbnail')
        picture_urls = []

        for picture in picture_containers:
            try:
                picture_url = picture.find('img')['content']
                picture_urls.append(picture_url)
            except KeyError:
                continue

        description = html_to_markdown(json_container['description'])

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
