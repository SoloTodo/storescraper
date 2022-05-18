import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import REFRIGERATOR, AIR_CONDITIONER, \
    VACUUM_CLEANER, OVEN, WASHING_MACHINE, HEADPHONES, \
    SOLID_STATE_DRIVE, MOUSE, KEYBOARD, MONITOR, TELEVISION, STEREO_SYSTEM, \
    CELL, WEARABLE, TABLET, PRINTER, NOTEBOOK, MEMORY_CARD, DISH_WASHER, \
    POWER_SUPPLY
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class SendTech(Store):
    @classmethod
    def categories(cls):
        return [
            AIR_CONDITIONER,
            REFRIGERATOR,
            VACUUM_CLEANER,
            OVEN,
            WASHING_MACHINE,
            HEADPHONES,
            SOLID_STATE_DRIVE,
            MOUSE,
            KEYBOARD,
            MONITOR,
            TELEVISION,
            STEREO_SYSTEM,
            CELL,
            WEARABLE,
            TABLET,
            PRINTER,
            NOTEBOOK,
            MEMORY_CARD,
            DISH_WASHER,
            POWER_SUPPLY,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['climatizacion/aire-acondicionado', AIR_CONDITIONER],
            ['climatizacion/purificador-de-aire', AIR_CONDITIONER],
            ['electro-hogar/aspiradoras', VACUUM_CLEANER],
            ['electro-hogar/hornos-electricos', OVEN],
            ['electro-hogar/microondas', OVEN],
            ['linea-blanca/lavadora/lavadoras', WASHING_MACHINE],
            ['linea-blanca/lavadora/secadoras', WASHING_MACHINE],
            ['linea-blanca/lavavajillas', DISH_WASHER],
            ['linea-blanca/refrigerador', REFRIGERATOR],
            ['gamer/accesorios-gaming', POWER_SUPPLY],
            ['gamer/auriculares', HEADPHONES],
            ['electro-tecno/almacenamiento/disco-duro-solidos',
             SOLID_STATE_DRIVE],
            ['gamer/mouse', MOUSE],
            ['gamer/teclados', KEYBOARD],
            ['tecnologia/audio-video/monitores', MONITOR],
            ['tecnologia/audio-video/parlantes', STEREO_SYSTEM],
            ['tecnologia/audio-video/smart-tv', TELEVISION],
            ['tecnologia/dispositivos-moviles/celulares', CELL],
            ['tecnologia/dispositivos-moviles/relojes', WEARABLE],
            ['tecnologia/dispositivos-moviles/tablets', TABLET],
            ['tecnologia/impresoras', PRINTER],
            ['tecnologia/notebook', NOTEBOOK],
            ['tecnologia/perifericos/auriculares-y-manos-libres', HEADPHONES],
            ['tecnologia/perifericos/mouse-accesorios', MOUSE],
            ['tecnologia/perifericos/tarjeta-de-memoria', MEMORY_CARD],
            ['tecnologia/perifericos/teclado', KEYBOARD],
        ]
        session = session_with_proxy(extra_args)
        products_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow')
                url_webpage = 'https://sendtech.cl/categoria-productos/{}' \
                              '/page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                products_containers = soup.find('ul', 'products')
                if not products_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + local_category)
                    break
                for container in products_containers.findAll('li'):
                    products_url = container.find('a')['href']
                    products_urls.append(products_url)
                page += 1
        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        sku_tag = soup.find('span', 'sku')

        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None

        if soup.find('p', 'price').text == '':
            return []

        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))

        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]

        add_to_cart_button = soup.find('button', {'name': 'add-to-cart'})

        if add_to_cart_button:
            stock = -1
        else:
            stock = 0

        part_number_container = soup.find('span', 'sku')

        if part_number_container:
            part_number = part_number_container.text.strip()
        else:
            part_number = None

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
            part_number=part_number
        )
        return [p]
