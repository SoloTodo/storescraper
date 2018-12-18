import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class NetNow(Store):
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
            ['25', 'Notebook'],  # Notebooks gamer
            ['28', 'Notebook'],  # Notebooks
            ['35', 'Notebook'],  # Ultradelgados
            ['31', 'Notebook'],  # Convertibles
            ['34', 'Notebook'],  # 2 en 1
            ['38', 'AllInOne'],  # All in One
            ['36', 'Monitor'],   # Monitors
            ['47', 'Tablet'],    # Tablets
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_id, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://www.netnow.cl/site/c/{}/category/' \
                               'productos?page={}'.format(category_id, page)
                json_data = json.loads(session.get(category_url).text)

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
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        sku = re.search(r'/p/(\d+)/', url).groups()[0]
        model = soup.find('div', 'producto-nombre').text.strip()
        part_number = soup.find('div', 'producto-subtitulo').text.strip()
        name = '{} ({})'.format(model, part_number)

        stock = int(re.search(
            r'STOCK: (\d+)',
            soup.find('div', 'producto-stock').text).groups()[0]
        )

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
