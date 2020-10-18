from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown
from storescraper.categories import PROCESSOR, MOTHERBOARD, VIDEO_CARD, \
    POWER_SUPPLY, SOLID_STATE_DRIVE, MOUSE


class Alfaomega(Store):
    @classmethod
    def categories(cls):
        return [
            PROCESSOR,
            MOTHERBOARD,
            VIDEO_CARD,
            POWER_SUPPLY,
            SOLID_STATE_DRIVE,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['procesador-2', PROCESSOR],
            ['placa-madre', MOTHERBOARD],
            ['tarjeta-de-video', VIDEO_CARD],
            ['disco-de-estado-solido', SOLID_STATE_DRIVE],
            ['fuente-de-poder', POWER_SUPPLY],
            ['mouse-y-teclados-2', MOUSE],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = 'https://aopc.cl/categoria/{}/?post_type=product'\
                .format(category_path)
            response = session.get(url)

            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.findAll('li', 'product-col')

            if not products:
                raise Exception('Empty path: {}'.format(url))

            for product in products:
                product_url = product.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h2', 'product_title').text.strip()
        sku_container = soup.find('span', 'sku')

        if not sku_container:
            return []

        sku = sku_container.text.strip()

        stock_text = soup.find('span', 'stock').text.strip()
        stock = 0
        if stock_text != 'Agotado':
            stock = int(stock_text.split(' ')[0])

        price_container = soup.find('p', 'price')

        if not price_container.text.strip():
            return []

        offer_price = Decimal(
            remove_words(price_container.find('ins').find('span').text))
        normal_price = Decimal(
            remove_words(price_container.find('del').find('span').text))

        picture_containers = soup.findAll('div', 'img-thumbnail')
        picture_urls = []

        for picture in picture_containers:
            try:
                picture_url = picture.find('img')['content']
                picture_urls.append(picture_url)
            except KeyError:
                continue

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
