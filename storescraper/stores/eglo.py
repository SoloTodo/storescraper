from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Eglo(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Ampolletas LED
            ['Ampolletas+LED', 'Lamp'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.eglo.cl/productos?' \
                           'subgrupo_desc_buscar%5B%5D={}'.format(
                               category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            product_containers = soup.findAll('div', 'product-preview-wrapper')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = 'http://www.eglo.cl' + \
                              container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'product-info__description').text.strip()
        sku = soup.find('div', 'product-info__title').find(
            'span').text.split(':')[1].strip()

        stock_container = soup.find('input', {'id': 'producto_cantidad'})
        if stock_container:
            stock = int(stock_container['max'])
        else:
            stock = 0

        price_container = soup.find('span', 'price-box__new')

        old_price_container = price_container.find('s')

        if old_price_container:
            old_price = Decimal(remove_words(old_price_container.text))
            price = (old_price * Decimal('0.9')).quantize(0)
        else:
            price = Decimal(remove_words(price_container.text))

        description = html_to_markdown(str(soup.find('div', 'tab-content')),
                                       'http://www.eglo.cl')

        picture_containers = soup.findAll('a', 'swiper-slide')

        if picture_containers:
            picture_urls = []
            for container in picture_containers:
                picture_url = container.find('img')['src']
                picture_urls.append(picture_url)
        else:
            picture_urls = [soup.find('div', 'product-main-'
                                             'image__item').img['src']]

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
