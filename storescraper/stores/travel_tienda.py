import json
import logging
import re
import urllib.parse
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL, WEARABLE, TELEVISION, \
    STEREO_SYSTEM, TABLET, MONITOR, WASHING_MACHINE, REFRIGERATOR, \
    VACUUM_CLEANER, OVEN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class TravelTienda(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            WEARABLE,
            TELEVISION,
            STEREO_SYSTEM,
            TABLET,
            MONITOR,
            WASHING_MACHINE,
            REFRIGERATOR,
            VACUUM_CLEANER,
            OVEN

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['carrusel-categorias-tienda/smartphones?N=3842720512',
             CELL],
            ['relojes/smartwatch?N=816923966', WEARABLE],
            ['tv/televisores?N=2722336774', TELEVISION],
            ['tv/sistemas-de-sonido-tv?N=2234300147',
             STEREO_SYSTEM],
            ['carrusel-categorias-tienda/audio?N=4064311224',
             STEREO_SYSTEM],
            ['computación/tablets?N=2934181475', TABLET],
            ['gamer/monitor-gamer?N=2871236375', MONITOR],
            ['categorías-redondo/lavadoras?N=2620100069',
             WASHING_MACHINE],
            ['línea-blanca/secadoras?N=394354836', WASHING_MACHINE],
            ['línea-blanca/refrigeradores?N=306745319',
             REFRIGERATOR],
            ['electrodomésticos/aspiradora-robot?N=2553914886',
             VACUUM_CLEANER],
            ['electrodomésticos/hornos-electricos-y-microondas?N=831669398',
             OVEN]
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 0
            url_webpage = r'https://tienda.travel.cl/category/{}+' \
                          r'3479876154&Nr=AND(sku.availabilityStatus:' \
                          r'INSTOCK)&maxItems=18&No={}'.format(url_extension,
                                                               page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            data = soup.find('body').find('script').text
            data_clean = urllib.parse.unquote(
                re.search(r'window.state = JSON.parse\(decodeURI\((.+)\)\)',
                          data).groups()[0])
            json_container = json.loads(data_clean[1:-1])
            category_path = \
                json_container['clientRepository']['context']['global'][
                    'path'].split('/')[-1]
            product_container = \
                list(json_container['searchRepository']['pages'].values())[0][
                    'results']['records']
            if not product_container:
                if page == 0:
                    logging.warning('Empty category' + url_extension)
                break
            for container in product_container:
                product_url = container['attributes']['product.route'][0]
                product_urls.append(
                    'https://tienda.travel.cl/' + category_path + product_url)
            page += 18
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_json = json.loads(
            soup.find('script', {'data-name': 'occ-structured-data'}).text)[0]
        data = soup.find('body').find('script').text

        data_clean = urllib.parse.unquote(
            re.search(r'window.state = JSON.parse\(decodeURI\((.+)\)\)',
                      data).groups()[0])
        json_container = list(
            json.loads(data_clean[1:-1])['catalogRepository'][
                'products'].values())[0]
        name = product_json['name']
        sku = product_json['sku']
        stock = -1
        normal_price = Decimal(product_json['offers']['price'])
        offer_price = Decimal(
            json_container['listPrices']['tiendaBancoDeChile'])
        picture_urls = ['https://tienda.travel.cl' + picture for picture in
                        json_container['fullImageURLs']]

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
            picture_urls=picture_urls
        )

        return [p]
