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
        url_extenisons = [
            TELEVISION
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extenisons:
            if local_category != category:
                continue
            page = 1
            while True:
                if page >= 16:
                    raise Exception('Page overflow')

                url_webpage = 'https://www.max.com.gt/catalogsearch/result/' \
                              'index/?category=&marca=7&p={}&q=LG'.format(page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category')
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in product_urls:
                        return product_urls
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        sku_container = soup.find('h6', 'sku')
        if sku_container:
            sku = sku_container.text.strip()
        else:
            sku = soup.find('input', {'name': 'product'})['value']

        name = '{} ({})'.format(soup.find('h1').text.strip(), sku)

        if soup.find('input', {'id': 'qty_stock'}):
            stock = int(soup.find('input', {'id': 'qty_stock'})['value'])
        else:
            stock = -1

        price_container = soup.find('span', {'itemprop': 'price'})
        price = Decimal(price_container.text.replace('Q', '').replace(',', ''))

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', 'fancybox-button')]
        description = html_to_markdown(
            str(soup.find('div', 'tab-product-detail')))

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
            'GTQ',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
