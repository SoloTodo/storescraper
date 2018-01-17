from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Syd(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Ram',
            'Tablet',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'http://syd.cl'

        category_paths = [
            ['/collection/macbook-pro-13', 'Notebook'],
            ['/collection/macbook-pro-15', 'Notebook'],
            ['/collection/macbook-air', 'Notebook'],
            # ['/computadoras/monitores', 'Monitor'],
            ['/collection/memorias', 'Ram'],
            # ['/ipodiphoneipad/ipad_retina', 'Tablet'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = url_base + category_path

            response = session.get(category_url)

            if response.url != category_url:
                raise Exception('Invalid category: ' + category_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            titles = soup.findAll('div', 'eg_product_card')

            if not titles:
                raise Exception('Empty category: ' + category_url)

            for title in titles:
                product_link = title.find('a')
                product_url = url_base + product_link['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h2').text
        sku = soup.find('select', 'form-control hidden').option['data-sku']
        part_number = sku
        price = Decimal(remove_words(soup.find(
            'select', 'form-control hidden').option['data-final_price']))

        description = soup.find('div', 'row text-justify')
        description = description.findAll('p')
        description = html_to_markdown(str(description))

        picture_urls = [soup.find(
            'img', 'img-thumbnail mk_main_img img-responsive')['src']]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'CLP',
            sku=sku,
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
