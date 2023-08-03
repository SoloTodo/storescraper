from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, GAMING_CHAIR, HEADPHONES, \
    KEYBOARD, MONITOR, NOTEBOOK, PRINTER, STEREO_SYSTEM, TABLET, TELEVISION, \
    VIDEO_GAME_CONSOLE, WEARABLE, RAM, MOUSE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, session_with_proxy


class Dreamtec(StoreWithUrlExtensions):
    url_extensions = [
        ['gamer-zone/accesorios-gamer-zone', MOUSE],
        ['gamer-zone/audifonos-gamer-zone', HEADPHONES],
        ['gamer-zone/audio', STEREO_SYSTEM],
        ['gamer-zone/consolas', VIDEO_GAME_CONSOLE],
        ['gamer-zone/monitores-gamer-zone', MONITOR],
        ['gamer-zone/notebooks-gamer-zone', NOTEBOOK],
        ['gamer-zone/sillas-gamer', GAMING_CHAIR],
        ['home-office/accesorios-home-office', KEYBOARD],
        ['home-office/all-in-one', ALL_IN_ONE],
        ['home-office/impresoras', PRINTER],
        ['home-office/monitores', MONITOR],
        ['home-office/notebooks', NOTEBOOK],
        ['smart-home/parlantes', STEREO_SYSTEM],
        ['smart-home/smart-tv', TELEVISION],
        ['smart-home/smart-watch', WEARABLE],
        ['smart-home/tablets', TABLET],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
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
        sku_detalle_tags = soup.findAll('span', 'sku-detalle')
        sku = str(sku_detalle_tags[0].find('strong').text)

        if len(sku_detalle_tags) == 3:
            part_number = str(sku_detalle_tags[1].find('strong').text)
        else:
            part_number = None

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
            part_number=part_number,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
