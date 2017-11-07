from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Tottus(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'http://www.tottus.cl'

        category_paths = [
            ['Electro-Hogar-Electro-TV/_/N-psmyna', 'Television'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = '{}/tottus/browse/{}'.format(url_base,
                                                        category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            product_containers = soup.findAll(
                'div', 'item-product-caption')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = container.findAll('a')[3]['href'].split('?')[0]
                product_url = '{}{}'.format(url_base, product_url)
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'title').find('h5').text.strip()
        sku = soup.find('input', {
            'name': '/atg/commerce/order/purchase/CartModifierFormHandler.'
                    'items[0].productId'})['value'].strip()

        if len(soup.findAll('div', 'out-of-stock')) == 2:
            stock = 0
        else:
            stock = -1

        prices_container = soup.find('div', 'price-selector')

        offer_price_container = prices_container.find('span', 'red')

        if offer_price_container:
            price = Decimal(remove_words(
                offer_price_container.text
            ))
        else:
            price = Decimal(remove_words(
                prices_container.find('span', 'active-price').find('span').text
            ))

        description = html_to_markdown(str(soup.find('div', {'id': 'tab_1'})))

        picture_urls = ['http://s7d2.scene7.com/is/image/Tottus/{}?scl=1.0'
                        ''.format(sku)]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
