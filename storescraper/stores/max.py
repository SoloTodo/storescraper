import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import TELEVISION


class Max(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        if category != TELEVISION:
            return []
        page = 1
        while True:
            if page >= 16:
                raise Exception('Page overflow')

            url_webpage = 'https://www.max.com.gt/marcas/productos-lg/' \
                'tv-lg?p={}'.format(page)
            print(url_webpage)
            data = session.get(url_webpage, timeout=30).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('li',
                                              'item product product-item')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category')
                break
            for container in product_containers:
                product_url = container.find('a')['href']
                print(product_url)
                if product_url in product_urls:
                    return product_urls
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url, timeout=30).text
        soup = BeautifulSoup(data, 'html.parser')
        name = soup.find('h1', 'page-title').text.strip()
        key = soup.find('input', {'id': 'getproductid'})['value']
        sku = soup.find('div', {'itemprop': 'sku'}).text

        if soup.find('div', 'stock available'):
            stock = -1
        else:
            stock = 0

        price_container = soup.find('span', {'data-price-type': 'finalPrice'})
        price = Decimal(price_container.text.replace('Q', '').replace(',', ''))
        picture_container = json.loads(
            soup.find('div', 'product media').find('script', {
                'type': 'text/x-magento-init'}).text)[
            '[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery'][
            'data']

        picture_urls = [tag['img'] for tag in picture_container]
        description = html_to_markdown(
            str(soup.find('table', {'id': 'product-attribute-specs-table'})))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'GTQ',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
