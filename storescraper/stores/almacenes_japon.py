from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class AlmacenesJapon(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            url_webpage = 'https://almacenesjapon.com/brand/53-lg?' \
                          'page={}'.format(page)
            print(url_webpage)

            if page > 20:
                raise Exception('page overflow: ' + url_webpage)

            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div',
                                              'ajax_block_product')

            if not product_containers:
                if page == 1:
                    raise Exception('No products found: ' + url_webpage)
                break

            for product in product_containers:
                product_url = product.find('a')['href']
                product_urls.append(product_url)
            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        if response.status_code == 403:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-detail-name').text.strip()
        sku = soup.find('meta', {'property': 'product:retailer_item_id'})[
            'content']

        if soup.find('link', {'itemprop': 'availability'})['href'] \
                == 'https://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('h4', {'itemprop': 'price'})['content'])

        picture_urls = [soup.find('meta', {'property': 'og:image'})['content']]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'full_spec'})))

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
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
