from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR, VIDEO_GAME_CONSOLE, \
    HEADPHONES, MOUSE, KEYBOARD, EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, \
    MEMORY_CARD, STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class Weplay(StoreWithUrlExtensions):
    url_extensions = [
        ['consolas.html', VIDEO_GAME_CONSOLE],
        ['computacion/audifonos-gamer.html', HEADPHONES],
        ['tecnologia/audifonos.html', HEADPHONES],
        ['computacion/teclados.html', KEYBOARD],
        ['tecnologia/teclados-tecnologia.html', KEYBOARD],
        ['computacion/discos-duros-externos.html', EXTERNAL_STORAGE_DRIVE],
        ['computacion/mouse.html', MOUSE],
        ['computacion/pendrives.html', USB_FLASH_DRIVE],
        ['computacion/tarjetas-de-memoria.html', MEMORY_CARD],
        ['tecnologia/parlantes.html', STEREO_SYSTEM],
        ['computacion/sillas-gamer.html', GAMING_CHAIR]
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            if page > 20:
                raise Exception('Page overflow: ' + url_extension)

            url = 'https://www.weplay.cl/{}?p={}'.format(
                url_extension, page)
            print(url)

            response = session.get(url).text
            soup = BeautifulSoup(response, 'html.parser')
            products = soup.findAll('a', 'product-item-link')

            if not products:
                return product_urls

            for product in products:
                product_url = product['href']

                if product_url in product_urls:
                    return product_urls

                product_urls.append(product_url)

            page += 1

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name_tag = soup.find('span', {'itemprop': 'name'})

        if not name_tag:
            return []

        name = name_tag.text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()

        web_stock = True

        if soup.find('p', 'out-of-stock'):
            web_stock = False

        store_stock = False

        for sucursal in soup.find('div', 'stock-manager').findAll('tr'):
            if 'Últimas unidades' in sucursal.text or 'Disponible' in \
                    sucursal.text:
                store_stock = True

        if store_stock or web_stock:
            stock = -1
        else:
            stock = 0
        price = Decimal(
            soup.find('meta', {'property': 'product:price:amount'})['content'])

        picture_urls = [tag['src'] for tag in
                        soup.findAll('img', 'gallery-placeholder__image')]
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
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
