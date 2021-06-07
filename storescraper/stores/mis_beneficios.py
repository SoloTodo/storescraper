import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class MisBeneficios(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow')
            url_webpage = 'https://ultimate-dot-acp-magento.appspot.com/' \
                          'full_text_search?q=lg&page_num={}&store_id=8' \
                          '&UUID=3a30338d-e35f-42e8-b98c-9ea16cca9012'. \
                format(page)
            data = session.get(url_webpage).text
            produts_data = json.loads(data)
            product_entries = produts_data['items']
            for entry in product_entries:
                product_url = entry['u']
                product_urls.append(product_url)
            if page >= produts_data['p']:
                break
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
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
