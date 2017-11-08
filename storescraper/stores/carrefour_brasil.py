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
            ['acessorios-de-informatica?termo=%3Arelevance%3A'
             'navegacao%3Apen-drive', 'UsbFlashDrive'],
            ['acessorios-de-informatica?termo=%3Arelevance%3A'
             'navegacao%3Ahd-externo', 'ExternalStorageDrive'],
            ['cameras-e-filmadoras?termo=%3Arelevance%3A'
             'navegacao%3Acartao-de-memoria', 'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.carrefour.com.br/' + category_path
            print(category_url)

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
        print(url)
        session = session_with_proxy(extra_args)
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
        picture_urls = [tag['data-zoom-image'] for tag in picture_tags]

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
