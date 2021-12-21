import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Woow(Store):
    @classmethod
    def categories(cls):
        return [
            WASHING_MACHINE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extension = [
            WASHING_MACHINE
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extension:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + local_category)
                url_webpage = 'https://ultimate-dot-acp-magento.appspot.com/' \
                              'full_text_search?q=lg&page_num={}&store_id=1&' \
                              'UUID=3a30338d-e35f-42e8-b98c-9ea16cca9012&' \
                              'sort_by=price_min_to_max&facets_required=1&' \
                              'related_search=1&with_product_attributes=1'. \
                    format(page)
                data = session.get(url_webpage).text
                product_containers = json.loads(data)
                if not product_containers or product_containers[
                        'total_results'] == 0:
                    break
                for container in product_containers['items']:
                    product_url = container['u']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)
        if not response.ok:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('div', 'price-box')['data-product-id']

        if soup.find('div', 'unavailable'):
            stock = 0
        else:
            stock = -1

        price = Decimal(soup.find('span', 'price').text.
                        split('\xa0')[1].replace('.', '').replace(',', '.'))
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'product media').findAll('img')
                        ]
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
            picture_urls=picture_urls
        )
        return [p]
