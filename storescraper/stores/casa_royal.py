import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import STORAGE_DRIVE, TABLET, STEREO_SYSTEM, \
    KEYBOARD, HEADPHONES, MOUSE, WEARABLE, VIDEO_GAME_CONSOLE, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, \
    session_with_proxy


class CasaRoyal(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            TABLET,
            STEREO_SYSTEM,
            KEYBOARD,
            HEADPHONES,
            MOUSE,
            WEARABLE,
            VIDEO_GAME_CONSOLE,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['audio/audifonos', HEADPHONES],
            ['audio/portable', STEREO_SYSTEM],
            ['audio/parlantes', STEREO_SYSTEM],
            ['audio/hogar', STEREO_SYSTEM],
            ['audifono', HEADPHONES],
            ['computacion/almacenamiento', STORAGE_DRIVE],
            ['computacion/tablet-y-proyectores/tablets', TABLET],
            ['computacion/accesorios-computacion/teclados-de-computacion',
             KEYBOARD],
            ['computacion/accesorios-computacion/mouse', MOUSE],
            ['computacion/accesorios-computacion/parlantes-de-computacion',
             STEREO_SYSTEM],
            ['computacion/accesorios-computacion/teclados', KEYBOARD],
            ['computacion/accesorios-computacion/parlantes-computacion',
             STEREO_SYSTEM],
            ['telefonia/wearables', WEARABLE],
            ['telefonia/audifonos', HEADPHONES],
            ['gamer/consolas', VIDEO_GAME_CONSOLE],
            ['gamer/audifonos-gamer', HEADPHONES],
            ['gamer/teclados-gamer', KEYBOARD],
            ['gamer/mouse-gamer', MOUSE],
            ['gamer/mouse', MOUSE],
            ['gamer/teclados', KEYBOARD],
            ['electronica-y-electricidad/computacion/mouse', MOUSE],
            ['electronica-y-electricidad/computacion/teclados-de-'
             'computacion.html', KEYBOARD],
            ['audio/microfonos', MICROPHONE]
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            done = False
            page = 1

            while not done:
                if page >= 15:
                    raise Exception('Page overflow: ' + category_path)

                category_url = 'https://www.casaroyal.cl/{}.html?p={}' \
                    .format(category_path, page)
                print(category_url)
                soup = BeautifulSoup(
                    session.get(category_url).text, 'html.parser')

                link_container = soup.find('ol', 'product-items')

                if not link_container:
                    if page == 1:
                        logging.warning('Empty category: ' + category_path)
                    break

                link_containers = soup.find('ol', 'product-items')

                for link_container in link_containers.findAll('li', 'item'):
                    product_url = link_container.find('a')['href']
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
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        name = soup.find('h1', 'page-title').text.strip()
        key = soup.find('input', {'name': 'product'})['value']
        sku = soup.find('div', 'sku').find('div', 'value').text.strip()

        if soup.find('p', 'redalert').text == 'Disponible':
            stock = -1
        else:
            stock = 0
            stock_container = soup.findAll('p', 'stocktienda')
            for stock in stock_container:
                if int(stock.text.split()[1]) > 0:
                    stock = -1
                    break
        price = Decimal(
            soup.find('meta', {'property': 'product:price:amount'})['content'])

        description = html_to_markdown(
            soup.find('div', 'productTabs-container').find(
                'div', {'id': 'description'}).text)

        if 'reacond' in name.lower() or 'reacond' in description.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        picture_urls = [tag['content'] for tag in
                        soup.findAll('meta', {'property': 'og:image'})]

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
            description=description,
            picture_urls=picture_urls,
            condition=condition
        )

        return [p]
