from decimal import Decimal

import demjson
from bs4 import BeautifulSoup

from storescraper.categories import GROCERIES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class LiderSupermarket(Store):
    @classmethod
    def categories(cls):
        return [
            GROCERIES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != GROCERIES:
            return []

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'solotodobot'

        # Get a starting page just to get the section IDs
        url = 'https://www.lider.cl/supermercado/category/a/_/N-qs16h7'
        res = session.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        sections = soup.find(
            'div', 'sidebar-categorias').findAll('div', 'panel-group')

        product_urls = []

        for section in sections:
            section_name = section.find('b').text.strip().upper()
            if section_name != 'DESPENSA':
                continue

            section_links = section.findAll('a')
            for section_link in section_links:
                print(section_link.text.strip())
                section_href = section_link['href']

                if section_href == '#':
                    print('=============')
                    continue

                if section_href.startswith('https://'):
                    url = section_href
                else:
                    url = 'https://www.lider.cl{}?Nrpp=1000'.format(
                        section_href)

                # print(url)
                res = session.get(url)
                soup = BeautifulSoup(res.text, 'html.parser')

                product_entries = soup.findAll('div', 'box-product')
                for product_entry in product_entries:
                    product_urls.append('https://www.lider.cl' +
                                        product_entry.find('a')['href'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'solotodobot'
        res = session.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        name = soup.find('h1').text.strip()

        json_tag = soup.find('script', {'type': 'application/ld+json'})

        if not json_tag:
            return []

        json_data = demjson.decode(json_tag.text)

        sku = json_data['sku']
        description = json_data['description']

        ean = None
        if 'gtin13' in json_data:
            ean = json_data['gtin13']
        if not check_ean13(ean):
            ean = None

        price = Decimal(json_data['offers']['lowPrice'])
        picture_urls = [json_data['image']]

        stock_url = 'https://www.lider.cl/supermercado/includes/inventory/' \
                    'inventoryInformation.jsp?productNumber={}&' \
                    'consolidate=true'.format(sku)
        stock_data = session.get(stock_url).json()

        if stock_data[0]['stockLevel'] == '0':
            stock = 0
        else:
            stock = -1

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
            'CLP',
            sku=sku,
            ean=ean,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
