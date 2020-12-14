from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words
from storescraper.categories import OVEN


class Hbt(Store):
    @classmethod
    def categories(cls):
        return [
            OVEN
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only interested in Samsung products
        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1
        done = False

        while not done:
            if page > 10:
                raise Exception('Page overflow')

            url = 'https://www.hbt.cl/catalogsearch/result/index/?q=samsung&' \
                  'p={}'.format(page)
            print(url)

            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            item_container = soup.find('ul', 'itemgrid')
            items = item_container.findAll('li', 'item')

            for item in items:
                product_url = item.find('a')['href']
                if product_url in product_urls:
                    done = True
                    break
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.54.0'
        response = session.get(url)

        if response.status_code == 500:
            return []

        data = response.text
        soup = BeautifulSoup(data, 'html.parser')

        if not soup.find('h1'):
            return []

        name = soup.find('h1').text.strip()
        sku = soup.find('div', 'sku').text.strip()

        price_block = soup.find('div', 'product-type-data')

        price_container = price_block.find('p', 'special-price')
        if not price_container:
            price_container = price_block.find('span', 'regular-price')

        price = Decimal(remove_words(price_container.find(
            'span', 'price').text))
        description = html_to_markdown(str(soup.find('div', 'p-text')))

        gallery = soup.find('div', {'id': 'amasty_gallery'})
        if not gallery:
            gallery = soup.find('div', 'product-image')

        picture_urls = [i['src'].strip() for i in
                        gallery.findAll('img')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
