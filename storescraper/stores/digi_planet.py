import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, KEYBOARD, MOUSE, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class DigiPlanet(Store):
    @classmethod
    def categories(cls):
        return [
            GAMING_CHAIR,
            KEYBOARD,
            MOUSE,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['sillas-gamer', GAMING_CHAIR],
            ['teclados-gamer', KEYBOARD],
            ['mouses-gamer', MOUSE],
            ['audifonos-gamer', HEADPHONES]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://digiplanet.cl/collections/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('a', 'grid-view-item__link')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['href']
                    product_urls.append('https://digiplanet.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-single__title').text
        sku = soup.find('span', 'shopify-product-reviews-badge')['data-id']
        if soup.find('link', {'itemprop': 'availability'})[
                'href'] == 'http://schema.org/OutOfStock':
            stock = 0
        else:
            stock = int(soup.find('span', {'id': 'counter_left'}).text)
        price = Decimal(
            soup.find('span', {'id': 'ProductPrice-product-template'})[
                'content'])
        picture_urls = ['https:' + tag['src'].split('?v')[0] for tag in
                        soup.find('div', 'thumbnails-wrapper').findAll('img')]
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
            picture_urls=picture_urls,
        )
        return [p]
