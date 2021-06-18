from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class LadyLee(Store):

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
                    raise Exception('Page overflow')

                url_webpage = 'https://ladylee.net/collections/all/' \
                              'marca_lg?page={}'.format(page)

                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'main_box')

                if not product_containers:
                    if page == 1:
                        raise Exception('Empty category: ' + url_webpage)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href'].split('/')[-1]
                    product_urls.append('https://ladylee.net/products/' +
                                        product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, allow_redirects=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        sku_container = soup.find('div', 'variant-sku')
        sku = sku_container.text.split(':')[1].strip()
        model_name_container = soup.find('div', 'description-first-part')
        name = soup.find('h1').text.strip()

        if model_name_container:
            model_name = model_name_container.find('p').text.split(
                ':')[1].strip()
            name = '{} ({})'.format(name, model_name)

        brand = soup.find('div', 'product-vendor').text.split(':')[1].strip()

        # We're only interested in LG products
        if brand == 'LG' and soup.find(
                'link', {'href': 'http://schema.org/InStock'}):
            stock = -1
        else:
            stock = 0

        price = soup.find('span', {'id': 'productPrice'})
        price = Decimal(price.text.replace('L', '').replace(',', ''))

        picture_urls = []

        for picture in soup.findAll('a', 'image-slide-link'):
            picture_url = 'https:' + picture['href']
            picture_urls.append(picture_url)

        description = html_to_markdown(str(
            soup.find('div', 'desc_blk')))

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
