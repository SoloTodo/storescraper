import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class TiendaClaro(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []

        if category == 'Cell':
            session = session_with_proxy(extra_args)
            offset = 0

            while True:
                category_url = 'https://tienda.clarochile.cl/webapp/wcs/' \
                               'stores/servlet/CategoryDisplay?categoryId=' \
                               '10008&pageSize=18&storeId=10151&beginIndex=' \
                               '{}'.format(offset)
                print(category_url)
                soup = BeautifulSoup(
                    session.get(category_url, verify=False).text,
                    'html.parser'
                )

                containers = soup.find(
                    'div', 'product_listing_container').findAll(
                    'div', 'product')

                if not containers:
                    if offset == 0:
                        raise Exception('Empty list')

                    break

                for container in containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                offset += 18

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url, verify=False).text,
                             'html.parser')

        base_name = soup.find('h1', 'main_header').text.strip()
        page_id = soup.find('meta', {'name': 'pageId'})['content']
        price_container = soup.find('span', {'id': 'offerPrice_{}'.format(
            page_id)})
        price = Decimal(remove_words(price_container.text))
        json_container = soup.find('div', {'id': 'entitledItem_{}'.format(
            page_id)})
        json_data = json.loads(json_container.text)
        description = html_to_markdown(
            str(soup.find('div', 'billing_method_div_custom')))
        description += '\n\n{}'.format(html_to_markdown(
            str(soup.find('div', 'descriptiveAttributes'))))
        products = []

        for product_entry in json_data:
            sku = product_entry['catentry_id']
            name = base_name

            for attribute_key in product_entry['Attributes'].keys():
                attribute, value = attribute_key.split('_|_')
                name += ' {} {}'.format(attribute, value)

            picture_urls = ['https://tienda.clarochile.cl{}'.format(
                product_entry['ItemImage467'])]

            products.append(Product(
                name,
                cls.__name__,
                'Cell',
                url,
                url,
                sku,
                -1,
                price,
                price,
                'CLP',
                sku=sku,
                cell_plan_name='Claro Prepago',
                description=description,
                picture_urls=picture_urls
            ))

        return products
