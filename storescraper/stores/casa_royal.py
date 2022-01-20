import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import STORAGE_DRIVE, TABLET, STEREO_SYSTEM, \
    KEYBOARD, HEADPHONES, MOUSE, WEARABLE, VIDEO_GAME_CONSOLE
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
            VIDEO_GAME_CONSOLE
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

                category_url = 'https://www.casaroyal.cl/{}.html?p={}'\
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

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', 'sku').find('span', 'value').text.strip()

        stock = -1

        price = soup.find('span', 'price').text.strip()
        price = Decimal(price.replace('$', '').replace('.', ''))

        description_panels = soup.find('div', 'tabs-panels')\
            .findAll('div', 'panel')

        description = html_to_markdown(
            str(description_panels[0]) + '\n' + str(description_panels[1]))

        if 'reacond' in name.lower() or 'reacond' in description.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        picture_urls = []

        for container in soup.find(
                'div', {'id': 'amasty_gallery'}).findAll('a'):
            try:
                picture_url = container['data-zoom-image']
                if picture_url.strip():
                    picture_urls.append(picture_url.strip())
            except KeyError:
                pass

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
            picture_urls=picture_urls,
            condition=condition
        )

        return [p]
