import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Igoa(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow')
                url_webpage = 'https://www.igoa.com.uy/categorias.php?b=lg&' \
                              'c=Todas+las+categor%C3%ADas&page={}' \
                    .format(page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'product-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + local_category)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if 'https://www.igoa.com.uy/' + product_url in \
                            product_urls:
                        return product_urls
                    product_urls.append(
                        'https://www.igoa.com.uy/' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('div', 'title').text
        if 'lg' not in name.lower():
            return []
        sku = url.split('=')[-1]
        stock = -1
        price = Decimal(soup.find('div', 'price-current').text.split()[-1])
        picture_urls = ['https://www.igoa.com.uy/' +
                        urllib.parse.quote(tag['src']) for tag in
                        soup.find('div', 'single-product-gallery-thumbs')
                            .findAll('img')]
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
            picture_urls=picture_urls
        )
        return [p]
