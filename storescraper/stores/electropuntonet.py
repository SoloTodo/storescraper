from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Electropuntonet(Store):
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
            ['Heladeras-y-Freezers/84', 'Refrigerator'],
            ['Acondicionado/17', 'AirConditioner'],
            ['Calefones/24', 'WaterHeater'],
            ['Lavarropas/11', 'WashingMachine'],
            ['Lavasecarropas/25', 'WashingMachine'],
            ['Secarropas-por-Calor/31', 'WashingMachine'],
            ['Secarropas-Centrifugo/34', 'WashingMachine'],
            ['Cocinas/12', 'Stove'],
            ['Anafes/23', 'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'http://www.electropuntonet.com/' \
                               'lista/productos/{}?pag={}'.format(
                                   category_path, page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')
                containers = soup.findAll('div', 'one-product')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for container in containers:
                    category_url = 'http://www.electropuntonet.com' + \
                          container.find('a')['href']
                    product_urls.append(category_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'prod-title').text.strip()
        sku = soup.find('input', {'name': 'id'})['value'].strip()

        price_string = soup.find('input', {'id': 'product_price'})['value']

        price = Decimal(price_string)

        panel_ids = ['First-desc', 'Specifications']
        description = ''
        for panel_id in panel_ids:
            panel = soup.find('div', {'id': panel_id})
            description += html_to_markdown(str(panel)) + '\n\n'

        picture_urls = []

        for container in soup.find('div', 'owl-carousel').findAll('div'):
            image_tag = container.find('img')
            if image_tag:
                picture_url = 'http://www.electropuntonet.com' + \
                              image_tag['data-zoom-image']
                picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
