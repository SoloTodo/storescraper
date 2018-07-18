from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class DavidAndJoseph(Store):
    @classmethod
    def categories(cls):
        return [
            'Monitor',
            'Headphones',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['video-pro/edicion-y-post-produccion/monitores-para-edicion',
             'Monitor'],
            ['audio-pro/audifonos', 'Headphones'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            category_url = 'http://davidandjoseph.cl/djcl/' + category_path

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            link_containers = soup.findAll('div', 'product-list-item')

            if not link_containers:
                raise Exception('Empty category: ' + category_url)

            for link_container in link_containers:
                product_urls.append(link_container.find('a')['href'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'heading-title').text.strip()
        sku = soup.find('span', {'itemprop': 'model'}).text.strip()
        part_number = sku

        if soup.find('span', 'outofstock'):
            stock = 0
        else:
            stock = -1

        price_cell = soup.find('li', 'price-new')

        if not price_cell:
            price_cell = soup.find('li', 'product-price')
        price = Decimal(remove_words(price_cell.string.split('$')[1]))

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'swipebox')]

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
