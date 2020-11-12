from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import MOTHERBOARD, RAM, PROCESSOR, VIDEO_CARD, \
    NOTEBOOK, TABLET, HEADPHONES, MOUSE, SOLID_STATE_DRIVE, KEYBOARD, \
    COMPUTER_CASE, MONITOR, STORAGE_DRIVE, POWER_SUPPLY, CPU_COOLER, CELL


class InfographicsSolutions(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            RAM,
            PROCESSOR,
            VIDEO_CARD,
            NOTEBOOK,
            TABLET,
            HEADPHONES,
            MOUSE,
            SOLID_STATE_DRIVE,
            KEYBOARD,
            COMPUTER_CASE,
            MONITOR,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            CPU_COOLER,
            CELL
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['equipos/portatiles', NOTEBOOK],
            ['tecnologia/smarthphone', CELL],
            ['tecnologia/tablet', TABLET],
            ['componentes-de-pc/placa-madre', MOTHERBOARD],
            ['componentes-de-pc/memorias-ram', RAM],
            ['componentes-de-pc/procesadores', PROCESSOR],
            ['componentes-de-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-de-pc/almacenamiento/discos-solidos',
             SOLID_STATE_DRIVE],
            ['componentes-de-pc/almacenamiento/discos-duros',
             STORAGE_DRIVE],
            ['componentes-de-pc/gabinetes', COMPUTER_CASE],
            ['componentes-de-pc/monitores', MONITOR],
            ['componentes-de-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-de-pc/refrigeracion', CPU_COOLER],
            ['accesorios-gamer/teclados', KEYBOARD],
            ['accesorios-gamer/headset-audifonos', HEADPHONES],
            ['accesorios-gamer/mouse', MOUSE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                url = 'https://infograsolutions.cl/categoria-producto/{}/' \
                      'page/{}/'.format(category_path, page)
                print(url)

                if page > 10:
                    raise Exception('Page overflow: ' + page)

                res = session.get(url)
                if res.status_code == 404:
                    if page == 1:
                        raise Exception('Invalid category: ' + url)
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                products = soup.findAll('div', 'product-grid-item')

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'product_title').text
        sku = soup.find('div', 'wd-wishlist-btn').find('a')['data-product-id']

        stock_container = soup.find('p', 'stock')

        if 'VENTA' in name.upper() and 'PRE' in name.upper():
            # Preventa
            stock = 0
        elif stock_container:
            stock_text = stock_container.text.split(' ')[0]
            if stock_text == 'Agotado':
                stock = 0
            else:
                stock = int(stock_text)
        else:
            stock = -1

        part_number_container = soup.find('span', 'sku')

        if part_number_container:
            part_number = part_number_container.text.strip()
        else:
            part_number = None

        price_container = soup.find('p', 'price')

        if price_container.find('ins'):
            price = Decimal(price_container.find('ins').text.replace(
                '$', '').replace('.', ''))
        else:
            price = Decimal(price_container.text.replace(
                '$', '').replace('.', ''))

        picture_containers = soup.findAll('div', 'product-image-wrap')
        picture_urls = [p.find('a')['href'] for p in picture_containers]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

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
            picture_urls=picture_urls,
            description=description,
            part_number=part_number
        )

        return [p]
