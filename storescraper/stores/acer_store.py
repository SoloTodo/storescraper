import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class AcerStore(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Tablet',
            'AllInOne',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['25/notebooks-gamer', 'Notebook'],
            ['28/notebook', 'Notebook'],
            ['89/chromebooks-chile', 'Notebook'],
            ['35/notebooks-ultralivianos', 'Notebook'],
            ['31/notebooks-convertible', 'Notebook'],
            ['34/notebooks-tablets-2-en-1', 'Notebook'],
            ['38/all-in-one', 'AllInOne'],
            ['36/monitores', 'Monitor'],
            ['47/tablets', 'Tablet'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_id, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                category_url = 'https://www.acerstore.cl/site/c/{}/' \
                               'productos?&page={}&orden=2'.format(
                                category_id, page)
                print(category_url)
                json_data = json.loads(session.get(category_url).text)

                if 'items' not in json_data['categorias'][0]:
                    break

                if 'categorias' not in json_data:
                    if page == 1:
                        raise Exception('Empty category: {}'.format(
                            category_id))

                    break

                for container in json_data['categorias'][0]['items']:
                    soup = BeautifulSoup(container, 'html.parser')
                    product_urls.append(soup.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        page_source = session.get(url)
        if len(page_source.history) and page_source.history[
                0].status_code == 301:
            return []
        soup = BeautifulSoup(page_source.text, 'html.parser')

        sku = re.search(r'/p/(\d+)/', url).groups()[0]
        model = soup.find('h1', 'producto-nombre').text.strip()
        part_number = soup.find('div', 'producto-subtitulo').text.strip()
        name = '{} ({})'.format(model, part_number)

        stock_container = soup.find('div', 'producto-stock')

        if stock_container:
            stock = int(re.search(
                r'STOCK: (\d+)',
                stock_container.text).groups()[0])
        else:
            stock = 0

        price = soup.find('div', 'producto-precio').text.split('(')[0]
        price = Decimal(remove_words(price))

        description = html_to_markdown(
            str(soup.find('table', 'producto-ficha-tabla')))

        picture_urls = []
        for tag in soup.findAll('div', 'producto-galeria-imagenes-item'):
            picture_tag = tag.find('a')
            if picture_tag:
                picture_urls.append(picture_tag['href'])

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
