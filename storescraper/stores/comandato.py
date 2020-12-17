import logging
import re
import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import OVEN, REFRIGERATOR, WASHING_MACHINE, \
    AIR_CONDITIONER, TELEVISION, CELL


class Comandato(Store):
    @classmethod
    def categories(cls):
        return [
            OVEN,
            REFRIGERATOR,
            WASHING_MACHINE,
            AIR_CONDITIONER,
            TELEVISION,
            CELL,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['ft=cocinas', OVEN],
            ['fq=C:/1000001/1000034/', REFRIGERATOR],
            ['fq=C:/1000001/1000039/', WASHING_MACHINE],
            ['fq=C:/1000002/', AIR_CONDITIONER],
            ['fq=C:/1000007/1000008/1000057/', TELEVISION],
            ['fq=C:/1000007/1000090/', CELL]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 10:
                    raise Exception('Page overflow')

                url = 'https://www.comandato.com/buscapagina?PS=24&' \
                      'sl=5fd2e9cb-dc33-4655-95e2-fc62e15a859a&cc=4&' \
                      'sm=0&{}&PageNumber={}'.format(
                       category_path, page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                products = soup.findAll('div', 'producto')

                if not products:
                    if page == 1:
                        logging.warning('Empty url {}'.format(url))
                    break

                for product in products:
                    if product.find('h3').find('strong').text != 'LG':
                        continue
                    product_url = product.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        data = response.text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('div', 'productDescriptionShort').text
        sku = soup.find('div', 'skuReference').text
        stock = 0
        if soup.find('link', {'itemprop': 'availability'})['href'] == \
                'http://schema.org/InStock':
            stock = -1

        pricing_data = re.search(r'vtex.events.addData\(([\S\s]+?)\);',
                                 data).groups()[0]
        pricing_data = json.loads(pricing_data)

        tax = Decimal('1.12')
        offer_price = Decimal(pricing_data['productPriceFrom'])*tax
        normal_price = Decimal(pricing_data['productListPriceFrom'])*tax

        picture_urls = [a['zoom'] for a in
                        soup.findAll('a', {'id': 'botaoZoom'})]

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
