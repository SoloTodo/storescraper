import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class PortatilChile(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'http://portatilchile.com/modules/blocklayered/' \
                   'blocklayered-ajax.php?id_category_layered={}&p={}'

        category_paths = [
            ['4', 'Notebook']
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                print(category_path, page)
                category_url = url_base.format(category_path, page)
                print(category_url)

                json_data = json.loads(session.get(category_url,
                                                   verify=False).text)
                soup = BeautifulSoup(json_data['productList'], 'html.parser')

                containers = soup.findAll('div', 'item')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                for product in containers:
                    product_url = product.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(session.get(url, verify=False).text,
                             'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value'].strip()
        part_number = soup.find('span', {'itemprop': 'sku'}).text.strip()

        unavailable_container = soup.find(
            'span', {'id': 'availability_value'}).string

        if unavailable_container:
            stock = 0
        else:
            stock = -1

        price_container = soup.find('span', {'id': 'our_price_display'})

        price = price_container.string.split('$')[1]
        price = Decimal(remove_words(price))

        condition = soup.find('link', {'itemprop': 'itemCondition'})['href']

        description = html_to_markdown(
            str(soup.find('div', 'page-product-box')))

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'fancybox')]

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
            picture_urls=picture_urls,
            condition=condition
        )

        return [p]
