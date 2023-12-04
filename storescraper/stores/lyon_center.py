import json
from decimal import Decimal
from bs4 import BeautifulSoup
from storescraper.categories import AIR_CONDITIONER
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import remove_words, session_with_proxy


class LyonCenter(StoreWithUrlExtensions):
    url_extensions = [
        ['lg', AIR_CONDITIONER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        url = 'https://lyoncenter.cl/product-brand/{}/'.format(url_extension)
        res = session.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        containers = soup.findAll('section', 'product')
        product_urls = []
        for container in containers:
            product_url = container.find('a')['href']
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text.strip()

        variations_form = soup.find('form', 'variations_form')
        products = []
        variations = json.loads(variations_form['data-product_variations'])
        for product in variations:
            variation_name = name + ' - ' + ' '.join(
                product['attributes'].values())
            key = str(product['variation_id'])
            sku = product.get('sku', None)
            price = Decimal(product['display_price'])
            picture_urls = [product['image']['url']]

            if product['is_in_stock']:
                stock = -1
            else:
                stock = 0

            p = Product(
                variation_name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                picture_urls=picture_urls
            )
            products.append(p)
        return products
