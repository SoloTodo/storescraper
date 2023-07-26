from decimal import Decimal
import base64
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, GAMING_CHAIR, HEADPHONES, \
    KEYBOARD, MONITOR, NOTEBOOK, PRINTER, STEREO_SYSTEM, TABLET, TELEVISION, \
    VIDEO_GAME_CONSOLE, WEARABLE, RAM, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class Dreamtec(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            NOTEBOOK,
            VIDEO_GAME_CONSOLE,
            HEADPHONES,
            GAMING_CHAIR,
            KEYBOARD,
            ALL_IN_ONE,
            PRINTER,
            TELEVISION,
            STEREO_SYSTEM,
            TABLET,
            WEARABLE,
            HEADPHONES,
            RAM,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['gamer-zone/audifonos-gamer-zone/', HEADPHONES],
            ['gamer-zone/consolas', VIDEO_GAME_CONSOLE],
            ['gamer-zone/monitores-gamer-zone', MONITOR],
            ['gamer-zone/notebooks-gamer-zone', NOTEBOOK],
            ['gamer-zone/sillas-gamer', GAMING_CHAIR],
            ['gamer-zone/accesorios-gamer-zone', MOUSE],
            ['home-office/all-in-one', ALL_IN_ONE],
            ['home-office/escaner', PRINTER],
            ['home-office/impresoras', PRINTER],
            ['home-office/macbook', NOTEBOOK],
            ['home-office/monitores', MONITOR],
            ['home-office/notebooks', NOTEBOOK],
            ['home-office/accesorios-home-office', RAM],
            ['smart-home/audifonos', HEADPHONES],
            ['smart-home/ipad', TABLET],
            ['smart-home/smart-tv', TELEVISION],
            ['smart-home/smart-watch', WEARABLE],
            ['smart-home/soundbar', STEREO_SYSTEM],
            ['smart-home/tablets', TABLET],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'http://www.dreamtec.cl/{}/' \
                ''.format(url_extension)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', 'foto-prod')
            if not product_containers:
                logging.warning('Empty category: ' + url_extension)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if 'No hemos podido encontrar el contenido' in soup.text:
            return []

        name = soup.find('h1').text.strip()
        description = soup.find('div', {'id': 'nav-home'}).text.strip()
        sku = str(soup.find('span', 'sku-detalle').find('strong').text)

        price_tag = soup.find('strong', 'fs-3')
        if not price_tag:
            return []
        normal_price = Decimal(remove_words(price_tag.text))
        offer_price = Decimal(remove_words(soup.find('h3', 'fs-1').text))

        stock_select = soup.find('select', {'id': 'select-cantidad'})
        options = stock_select.findAll('option')
        stock = int(options[-1]['value'])

        picture_urls = []

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
            picture_urls=picture_urls,
            description=description
        )
        return [p]
