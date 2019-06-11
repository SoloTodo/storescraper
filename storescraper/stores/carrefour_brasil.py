from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class CarrefourBrasil(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['pen-drive', 'UsbFlashDrive'],
            ['hd-externo', 'ExternalStorageDrive'],
            ['cartao-de-memoria', 'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.carrefour.com.br/' + category_path

            soup = BeautifulSoup(session.get(category_url).text,
                                 'html.parser')

            containers = soup.findAll('li', 'product')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = 'https://www.carrefour.com.br' + \
                              container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'})

        if not name:
            return []

        name = name.text.strip()

        stock = -1
        if soup.find('strong', 'text-not-product-avisme'):
            stock = 0

        price = soup.find('meta', {'itemprop': 'lowPrice'})
        if not price:
            price = soup.find('meta', {'itemprop': 'price'})

        normal_price = Decimal(price['content'])
        offer_price = normal_price

        sku = soup.find('span', {'itemprop': 'sku'}).text.split('.', 1)[1]

        description = html_to_markdown(str(
            soup.find('div',
                      'yCmsContentSlot productDetailsPageShortDescription')))

        picture_tags = soup.find('div', 'gallery-image').findAll('img')
        picture_urls = [tag['data-zoom-image'] for tag in picture_tags
                        if tag.has_attr('data-zoom-image')]

        if not picture_urls:
            picture_urls = None

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
            'BRL',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
