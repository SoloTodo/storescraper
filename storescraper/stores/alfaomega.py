import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import PROCESSOR, MOTHERBOARD, VIDEO_CARD, \
    POWER_SUPPLY, SOLID_STATE_DRIVE, COMPUTER_CASE, RAM, CPU_COOLER, \
    NOTEBOOK, USB_FLASH_DRIVE, PRINTER, MONITOR, KEYBOARD, \
    EXTERNAL_STORAGE_DRIVE, MEMORY_CARD


class Alfaomega(StoreWithUrlExtensions):
    url_extensions = [
        ['intel', PROCESSOR],
        ['ryzen', PROCESSOR],
        ['refrigeracion', CPU_COOLER],
        ['placas-intel', MOTHERBOARD],
        ['placas-amd', MOTHERBOARD],
        ['memorias', RAM],
        ['discos-ssd', SOLID_STATE_DRIVE],
        ['discos-externos', EXTERNAL_STORAGE_DRIVE],
        ['fuentes-de-poder', POWER_SUPPLY],
        ['gabinetes', COMPUTER_CASE],
        ['tarjetas-graficas', VIDEO_CARD],
        ['monitores', MONITOR],
        ['mouse-y-teclados', KEYBOARD],
        ['memorias-micro-sd', MEMORY_CARD],
        ['pendrive', USB_FLASH_DRIVE],
        ['notebooks', NOTEBOOK],
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
                raise Exception('Invalid section: ' + url)

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
