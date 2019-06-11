from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Cetrogar(Store):
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
            ['electrodomesticos/heladeras-y-freezers/heladeras.html',
             'Refrigerator'],
            ['electrodomesticos/heladeras-y-freezers/freezers.html',
             'Refrigerator'],
            ['electrodomesticos/climatizacion/aires-acondicionados.html',
             'AirConditioner'],
            # ['electrodomesticos/calefones.html',
            #  'WaterHeater'],
            ['electrodomesticos/lavarropas-secarropas/lavarropas.html',
             'WashingMachine'],
            ['electrodomesticos/lavarropas-secarropas/secarropas.html',
             'WashingMachine'],
            ['electrodomesticos/lavarropas-secarropas/lavasecarropas.html',
             'WashingMachine'],
            ['electrodomesticos/cocinas/cocinas.html',
             'Stove'],
            ['electrodomesticos/cocinas/anafes.html',
             'Stove'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.cetrogar.com.ar/{}'.format(
                category_path)
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.findAll('li', 'item')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('span', 'h1').text.strip()
        sku = soup.find('span', 'code').text.strip()
        key = sku

        price_string = soup.find('meta', {'itemprop': 'price'})['content']

        normal_price = Decimal(price_string)
        offer_price = normal_price

        description = ''

        for tab in soup.findAll('div', 'tab-content'):
            description += html_to_markdown(str(tab)) + '\n\n'

        picture_urls = []

        for tag in soup.findAll('img', 'gallery-image'):
            picture_url = tag['src']
            if picture_url not in picture_urls:
                picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            -1,
            normal_price,
            offer_price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
