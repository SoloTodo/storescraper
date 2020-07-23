import json
import urllib
import re

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Marcimex(Store):
    @classmethod
    def categories(cls):
        return [
            'AirConditioner',
            'Oven',
            'WashingMachine',
            'Refrigerator',
            'SteroSystem',
            'Television',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['C:/2/14/', 'AirConditioner'],
            ['C:/2/11/', 'Oven'],
            ['C:/2/12/', 'WashingMachine'],
            ['C:/2/13/', 'Refrigerator'],
            ['C:/3/28/', 'StereoSystem'],
            ['C:/3/29/', 'Television'],
            ['C:/5/50/', 'Oven']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                url = 'https://www.marcimex.com/buscapagina?fq={}&' \
                      'PS=12&sl=2d6db67e-7134-4424-be62-6bbea419c476&cc=12&' \
                      'sm=0&PageNumber={}&fq=B:2000002'.format(
                       urllib.parse.quote_plus(category_path), page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                products = soup.findAll('div', 'productVitrine')

                if not products:
                    if page == 1:
                        raise Exception('Empty url {}'.format(url))
                    else:
                        break

                for product in products:
                    product_url = product.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        scripts = soup.findAll('script')
        product_data = [s for s in scripts if 'var skuJson' in s.text]

        if product_data:
            product_data = product_data[0].text
        else:
            raise Exception('No Data')

        product_json = json.loads(re.search(
            r'var skuJson_0 = ([\S\s]+?);', product_data).groups()[0])

        name = product_json['name']
        sku = str(product_json['skus'][0]['sku'])
        stock = 0
        if product_json['available']:
            stock = -1

        tax = Decimal(1.12)
        normal_price = Decimal(product_json['skus'][0]['listPrice']/100)*tax
        offer_price = Decimal(product_json['skus'][0]['bestPrice']/100)*tax
        picture_urls = [product_json['skus'][0]['image']]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'caracteristicas'})))

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
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
