import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class OrbitalStore(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'Ram',
            'Monitor',
            'Processor',
            'VideoCard',
            'Motherboard',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://www.orbitalstore.mx/{}'

        url_extensions = [
            ['almacenamiento/hdd-pc.html', 'StorageDrive'],
            ['almacenamiento/ssd.html', 'SolidStateDrive'],
            ['desktop-pc/componentes/fuente-de-poder.html', 'PowerSupply']
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            category_url = url_base.format(url_extension)
            page = 1
            done = False

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                url = category_url + '?limit=30&p={}'.format(page)
                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                products = list(set(soup.findAll('h3', 'product-name')))

                if not products:
                    raise Exception('Empty category: ' + category_url)

                for product in products:
                    product_url = product.find('a')['href']
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
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('div', 'product-name').find('h1').text
        sku = soup.find('div', 'product_info_left').find('p').find('b').text

        stock = -1

        price = Decimal(soup.find('div', 'price-box').find('span', 'price').text.replace('$', '').replace(',', ''))

        picture_urls = []
        images = soup.find('ul', 'slides').findAll('li')

        for image in images:
            picture_urls.append(image.find('a')['href'])

        description = html_to_markdown(str(soup.find('div', 'short-description')))

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
            'MXN',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
