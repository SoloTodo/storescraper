import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import PROCESSOR, MOTHERBOARD, VIDEO_CARD, \
    POWER_SUPPLY, SOLID_STATE_DRIVE, COMPUTER_CASE, RAM, CPU_COOLER, \
    NOTEBOOK, USB_FLASH_DRIVE, PRINTER, MONITOR, KEYBOARD


class Alfaomega(StoreWithUrlExtensions):
    url_extensions = [
        ['procesador', PROCESSOR],
        ['procesador-2', PROCESSOR],
        ['refrigeracion', CPU_COOLER],
        ['placas-intel', MOTHERBOARD],
        ['placas-amd', MOTHERBOARD],
        ['memorias', RAM],
        ['tarjetas-graficas', VIDEO_CARD],
        ['tarjeta-de-video', VIDEO_CARD],
        ['discos-duros-almacenamiento', SOLID_STATE_DRIVE],
        ['disco-duros-para-pc', SOLID_STATE_DRIVE],
        ['discos-ssd', SOLID_STATE_DRIVE],
        ['disco-de-estado-solido', SOLID_STATE_DRIVE],
        ['disco-duro', SOLID_STATE_DRIVE],
        ['pendrive', USB_FLASH_DRIVE],
        ['gabinetes', COMPUTER_CASE],
        ['fuentes-de-poder', POWER_SUPPLY],
        ['mouse-y-teclados', KEYBOARD],
        ['mouse-y-teclados-componentes-partes-y-piezas', KEYBOARD],
        ['mouse-y-teclados-2', KEYBOARD],
        ['notebooks', NOTEBOOK],
        ['monitores', MONITOR],
        ['impresoras-y-suministros', PRINTER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        page = 1

        while True:
            url = 'https://aopc.cl/categoria/{}/page/{}'\
                .format(url_extension, page)
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
        sku = str(json_container['sku'])
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
