import urllib
from _decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class CasaDelAudio(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['127', 'Refrigerator'],
            ['101', 'AirConditioner'],
            ['17', 'WaterHeater'],
            ['4191', 'WashingMachine'],
            ['123', 'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = 'https://www.casadelaudio.com/Item/Search/?page=1&id={}&' \
                  'recsPerPage=1000&order=Price&sort=True&itemtype=Product&' \
                  'term=&getFilterData=True&filters=&fields=Name'.format(
                    category_path)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')

            containers = soup.findAll('li', 'item')

            if not containers:
                raise Exception('Empty category: ' + category_path)

            for container in containers:
                url = 'https://www.casadelaudio.com' + \
                      container.find('a')['href']
                product_urls.append(url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('span', {'itemprop': 'sku'}).text.strip()

        price_string = soup.find('span', {'itemprop': 'price'}).text

        normal_price = Decimal(price_string.replace('.', '').replace(
            '$', '').replace(',', '.'))
        offer_price = normal_price

        description = html_to_markdown(
            str(soup.find('div', {'id': 'my-tab-content'})))

        pictures_container = soup.find('div', {'id': 'g_thumbs'})

        if pictures_container:
            picture_urls = []
            for tag in pictures_container.findAll('a'):
                picture_url = 'https://www.casadelaudio.com' + \
                              urllib.parse.quote(tag['data-zoom-image'])
                picture_urls.append(picture_url)
        else:
            picture_urls = None

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            normal_price,
            offer_price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
