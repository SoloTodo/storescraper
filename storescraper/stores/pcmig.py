import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Pcmig(Store):
    @classmethod
    def categories(cls):
        return [
            # 'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            CPU_COOLER,
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            # 'Ups',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Monitor'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['discos-duros', 'StorageDrive'],
            ['unidades-ssd', 'SolidStateDrive'],
            ['tarjetas-madre', 'Motherboard'],
            ['procesadores', 'Processor'],
            ['enfriamiento/liquido-enfriamiento', CPU_COOLER],
            ['enfriamiento/aire-enfriamiento', CPU_COOLER],
            ['memorias-ram', 'Ram'],
            ['tarjetas-graficas', 'VideoCard'],
            ['fuentes', 'PowerSupply'],
            ['gabinetes', 'ComputerCase'],
            ['mouse-gaming', 'Mouse'],
            ['teclado-gaming', 'Keyboard'],
            ['monitores', 'Monitor']
        ]

        base_url = 'https://pcmig.com.mx/categoria-producto/{}/page/{}/'
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)
                print(url)

                if page >= 100:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_container = soup.find('div', 'products')

                if not product_container:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                products = product_container.findAll('div', 'product-wrapper')

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'

        page_source = session.get(url, allow_redirects=False).text
        soup = BeautifulSoup(page_source, 'html5lib')

        name = soup.find('h1', 'product_title').text
        sku = soup.find('input', {'id': 'comment_post_ID'})['value']

        if soup.find('p', 'in-stock'):
            stock = -1
        else:
            stock = 0

        price_container = soup.find('p', 'price')

        if price_container.find('ins'):
            price = price_container.find('ins').find(
                'span', 'woocommerce-Price-amount amount').text
        else:
            price = price_container.find(
                'span', 'woocommerce-Price-amount amount').text

        price = Decimal(price.replace('$', '').replace(',', ''))

        pictures = soup.findAll('li', 'yith_magnifier_thumbnail')
        picture_urls = [p.find('a')['href'] for p in pictures]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

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
            description=description,
        )

        return [p]
