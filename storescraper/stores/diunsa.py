import json
import urllib
import re

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Diunsa(Store):
    @classmethod
    def categories(cls):
        return [
            'Stove',
            'WashingMachine',
            'Refrigerator',
            'Oven',
            'StereoSystem',
            'Cell',
            'Television',
            'AirConditioner',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['C:/1/73/84/86/', 'Stove'],
            ['C:/1/73/84/88/', 'WashingMachine'],
            ['C:/1/73/84/85/', 'Refrigerator'],
            ['C:/1/73/74/75/', 'Oven'],
            ['C:/1/58/64/68/', 'StereoSystem'],
            ['C:/1/58/64/66/', 'StereoSystem'],
            ['C:/1/58/64/65/', 'StereoSystem'],
            ['C:/1/58/69/', 'Cell'],
            ['C:/1/58/71/', 'Television'],
            ['C:/1/73/119/', 'AirConditioner'],
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

                url = 'https://www.diunsa.hn/buscapagina?fq={}&PS=12&' \
                      'sl=47de5394-cc68-404f-93ee-dca7e0b26b7f&cc=12&' \
                      'O=OrderByReleaseDateDESC&sm=0&PageNumber={}' \
                      '&fq=B:2000683'.format(
                       urllib.parse.quote_plus(category_path), page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                products = soup.findAll('div', 'contentShelve')

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

        price = Decimal(product_json['skus'][0]['bestPrice']/100)
        picture_urls = [
            a['zoom'] for a in soup.findAll('a', {'id': 'botaoZoom'})]

        description = html_to_markdown(
            str(soup.find('div', 'productDescription')))

        part_number = soup.find('div', 'productReference').text.strip()

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number
        )

        return [p]
