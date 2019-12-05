from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Tecnofacil(Store):
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
            ('tv-y-video', 'Television'),
            ('audio', 'StereoSystem'),
            ('celulares', 'Cell'),
            ('linea-blanca', 'Refrigerator'),
            ('electrodomesticos', 'Oven')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False

            while True:
                if page >= 20:
                    raise Exception('Page overflow')

                url = 'https://www.tecnofacil.com.gt/{}?p={}'\
                    .format(category_path, page)
                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                print(url)

                for container in soup.findAll('div', 'products'):
                    product_url = container.find('a')['href']

                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')
        sku_container = soup.find('h6', 'sku')

        if not sku_container:
            return []

        sku = sku_container.text.strip()
        name = "{} ({})".format(soup.find('div', 'product-name')
                                .find('h1').text.strip(), sku)

        if soup.find('p', 'availability').find('span').text.strip() \
                == 'En existencia':
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('div', 'price-box').find('span', 'price')
                        .text.replace('Q', '').replace(',', ''))

        picture_urls = [soup.find('p', 'product-image').find('a')['href']]
        description = html_to_markdown(str(
            soup.find('div', {'id': 'product_tabs_description_contents'})))

        description += '\n\n'

        description += html_to_markdown(str(
            soup.find('div', {'id': 'product_tabs_additional_contents'})))

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
            'GTQ',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
