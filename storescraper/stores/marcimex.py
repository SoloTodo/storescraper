import json
import logging
import urllib
import re

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import AIR_CONDITIONER, OVEN, WASHING_MACHINE, \
    REFRIGERATOR, STEREO_SYSTEM, TELEVISION


class Marcimex(Store):
    @classmethod
    def categories(cls):
        return [
            AIR_CONDITIONER,
            OVEN,
            WASHING_MACHINE,
            REFRIGERATOR,
            STEREO_SYSTEM,
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['C:/2/14/', AIR_CONDITIONER],
            ['C:/2/11/', OVEN],
            ['C:/2/12/', WASHING_MACHINE],
            ['C:/2/13/', REFRIGERATOR],
            ['C:/3/28/', STEREO_SYSTEM],
            ['C:/3/29/', TELEVISION],
            ['C:/5/50/', OVEN]
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
                        logging.warning('Empty url {}'.format(url))
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
        stock = -1
        if not product_json['available']:
            # Products with no stock have wrong prices for some reason
            return []
        price = (
            Decimal(product_json['skus'][0]['bestPrice']/100.0) +
            Decimal(product_json['skus'][0]['taxAsInt']/100.0)
            ).quantize(Decimal('.01'))
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
            price,
            price,
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
