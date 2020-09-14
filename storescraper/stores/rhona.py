import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Rhona(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Ampolletas LED
            ['catalogo/5/iluminacion/42' +
             '/iluminacion-led/120/ampolletas-led.html/', 'Lamp'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 0
            while True:
                category_url = 'https://www.rhona.cl/{}{}'.format(
                    category_path, page
                )

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                product_containers = soup.findAll('div', 'blockProducto')
                if len(product_containers) == 0:
                    if page == 0:
                        raise Exception('Empty category: ' + category_url)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'titulo').text.strip()

        identifier = soup.find('div', 'identif').text.strip()
        sku, part_number = \
            re.search(r'Código Rhona: (\d+) \| Código Fabricante: (.+)',
                      identifier).groups()

        price = soup.find('span', 'verde')

        if not price:
            stock = 0
            price = Decimal(0)
        else:
            stock = -1
            price = Decimal(remove_words(price.string))

        description = html_to_markdown(str(soup.find('ul', {'id': 'tab1'})))

        picture_urls = [tag['href'] for tag in
                        soup.find('div', 'masFotos').findAll('a')]

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
