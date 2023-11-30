from bs4 import BeautifulSoup
from storescraper.categories import CASE_FAN, COMPUTER_CASE, \
    CPU_COOLER, GAMING_CHAIR, HEADPHONES, KEYBOARD, MONITOR, \
    MOTHERBOARD, MOUSE, POWER_SUPPLY, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, STORAGE_DRIVE, VIDEO_CARD, KEYBOARD_MOUSE_COMBO
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class GigaSystem(StoreWithUrlExtensions):
    url_extensions = [
        ['discos-duros', STORAGE_DRIVE],
        ['ram', RAM],
        ['ssd-unidades-de-estado-solido', SOLID_STATE_DRIVE],
        ['cooler-cpu', CPU_COOLER],
        ['fuentes-de-poder', POWER_SUPPLY],
        ['gabinetes', COMPUTER_CASE],
        ['placa-madre', MOTHERBOARD],
        ['procesador', PROCESSOR],
        ['tarjetas-de-video', VIDEO_CARD],
        ['ventilador', CASE_FAN],
        ['auriculares', HEADPHONES],
        ['monitores', MONITOR],
        ['mouse', MOUSE],
        ['pack-teclado-mouse', KEYBOARD_MOUSE_COMBO],
        ['sillas-gamer', GAMING_CHAIR],
        ['teclados', KEYBOARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        url_webpage = 'https://gigasystem.cl/Categoria-Producto/{}'.format(
                          url_extension)
        print(url_webpage)
        response = session.get(url_webpage)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_containers = soup.findAll('a', 'woocommerce-LoopProduct-link')

        for container in product_containers:
            product_url = container['href']
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('?p=')[-1]
        name = soup.find('h1', 'product_title').text.strip()

        input_qty = soup.find('input', 'qty')
        if input_qty:
            if 'max' in input_qty.attrs and input_qty['max']:
                stock = int(input_qty['max'])
            else:
                stock = -1
        else:
            stock = 0

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
            picture_urls=picture_urls,
            description=description,
        )
        return [p]