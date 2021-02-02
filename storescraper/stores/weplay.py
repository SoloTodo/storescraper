from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR, VIDEO_GAME_CONSOLE, \
    HEADPHONES, MOUSE, KEYBOARD, EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, \
    MEMORY_CARD, STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Weplay(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_GAME_CONSOLE,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            EXTERNAL_STORAGE_DRIVE,
            USB_FLASH_DRIVE,
            MEMORY_CARD,
            STEREO_SYSTEM,
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # ['consolas/consolas3ds.html', VIDEO_GAME_CONSOLE'],
            ['consolas/consolas-switch.html', VIDEO_GAME_CONSOLE],
            # ['consolas/consolasps4.html', VIDEO_GAME_CONSOLE'],
            # ['consolas/consolasxboxone.html', VIDEO_GAME_CONSOLE'],
            ['computacion/audifonosgamer.html', HEADPHONES],
            ['computacion/teclados.html', KEYBOARD],
            ['computacion/discosdurosexternos.html', EXTERNAL_STORAGE_DRIVE],
            ['computacion/mouse.html', MOUSE],
            ['computacion/pendrives.html', USB_FLASH_DRIVE],
            ['computacion/tarjetasdememoria.html', MEMORY_CARD],
            ['computacion/parlantescomputacion.html', STEREO_SYSTEM],
            ['computacion/sillasgamer.html', GAMING_CHAIR]
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_path, local_category = e

            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page > 20:
                    raise Exception('Page overflow: ' + category_path)

                url = 'https://www.weplay.cl/{}?p={}'.format(
                    category_path, page)
                print(url)

                response = session.get(url).text
                soup = BeautifulSoup(response, 'html.parser')
                products = soup.findAll('a', 'product-item-link')

                if not products:
                    break

                for product in products:
                    product_url = product['href']

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

        soup = BeautifulSoup(response.text, 'html.parser')
        # import ipdb
        # ipdb.set_trace()
        name = soup.find('span', {'itemprop': 'name'}).text.strip()
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
            soup.find('span', 'price')
                .text.replace('$', '').replace('.', ''))

        picture_urls = [tag['src'] for tag in soup.findAll('img','gallery-placeholder__image')]
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
