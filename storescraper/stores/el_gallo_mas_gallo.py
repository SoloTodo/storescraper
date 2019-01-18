import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class ElGalloMasGallo(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'AirConditioner',
            'WashingMachine',
            'OpticalDiskPlayer',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('273_pantallas', 'Television'),
            ('268_minicomponentes', 'StereoSystem'),
            # ('274_parlantes', 'StereoSystem'),
            # ('282_sistemas-de-audio-y-accesorios', 'StereoSystem'),
            ('253_celulares', 'Cell'),
            ('280_refrigeradoras', 'Refrigerator'),
            ('260_hornos-y-extractores', 'Oven'),
            ('247_aires-acondicionados', 'AirConditioner'),
            ('265_lavadoras-y-secadoras', 'WashingMachine'),
            # ('281_reproductores-de-video-y-proyectores', 'OpticalDiskPlayer')
            ('255_cocinas', 'Stove')
        ]

        session = session_with_proxy(extra_args)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 '
                          'Safari/537.36'
        })
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'http://catalogoni.gallomasgallo.com/' \
                      '{}#/pageSize=120&orderBy=0&pageNumber={}'\
                      .format(category_path, page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                containers = soup.findAll('div', 'product-item')

                for container in containers:
                    product_url = 'http://catalogoni.gallomasgallo.com{}'\
                        .format(container.find('a')['href'])

                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 '
                          'Safari/537.36'
        })

        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('span', {'itemprop': 'sku'}).text.strip()

        return []
