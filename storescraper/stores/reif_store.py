import demjson
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class ReifStore(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Cell',
            'Tablet',
            'Headphones',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['88-portatil', 'Notebook'],
            ['14-iphone', 'Cell'],
            ['12-ipad', 'Tablet'],
            ['127-audifonos', 'Headphones'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.reifstore.cl/{}?p={}'.format(
                    category_path, page
                )

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                response = session.get(category_url)

                if response.url != category_url:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                for container in soup.findAll('div', 'product-container'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text.strip()
        part_number = soup.find('span', {'itemprop': 'sku'})['content']
        sku = soup.find('input', {'name': 'id_product'})['value']

        availability = soup.find('link', {'itemprop': 'availability'})

        if availability and \
                availability['href'] == 'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('span', {'itemprop': 'price'})['content'])

        picture_urls = []

        for tag in soup.find('ul', {'id': 'thumbs_list_frame'}).findAll('a'):
            picture_url = demjson.decode(
                re.search(r'rel="(.+?)"', str(tag)).groups()[0])['largeimage']
            picture_urls.append(picture_url)

        description = html_to_markdown(
            str(soup.find('section', 'page-product-box')))

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
