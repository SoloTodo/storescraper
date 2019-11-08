import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class HpOnline(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Printer',
            'AllInOne',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['notebooks', 'Notebook'],
            ['impresoras', 'Printer'],
            ['desktops/desktops-all-in-one', 'AllInOne'],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.hponline.cl/c/{}?page={}' \
                               '&lazy=true'.format(category_path, page)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')
                product_cells = soup.findAll('div', 'catalogue-product')

                if not product_cells:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for cell in product_cells:
                    product_url = 'https://www.hponline.cl' + \
                                  cell.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        response = session.get(url)

        if response.url != url or response.status_code == 404:
            return []

        page_source = response.text

        pricing_str = re.search(r'hpContainerPushData = ([\S\s]+?);',
                                page_source).groups()[0]
        pricing_data = json.loads(pricing_str)['ecommerce'][
            'detail']['products'][0]

        name = pricing_data['name']
        part_number = pricing_data['id']
        price = Decimal(pricing_data['price'])

        soup = BeautifulSoup(page_source, 'html.parser')
        sku = soup.find('meta', {'itemprop': 'sku'})['content']

        description = html_to_markdown(
            str(soup.find('div', 'product-description-container')))

        picture_urls = ['https:' + tag.find('img')['data-lazy'] for tag in
                        soup.findAll('div', {'id': 'image-product'})]

        availability_container = soup.find('link',
                                           {'itemprop': 'availability'})

        if not availability_container:
            stock = 0
        elif availability_container['href'] == 'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
