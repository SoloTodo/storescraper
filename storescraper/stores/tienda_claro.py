from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class TiendaClaro(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []

        if category == 'Cell':
            session = session_with_proxy(extra_args)
            page = 1

            while True:
                category_url = 'http://tienda.clarochile.cl/?limit=36&p=' + \
                               str(page)
                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                done = False

                for container in soup.findAll('div', 'item'):
                    product_url = container.find('a')['href']

                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h2').text.strip()
        sku = soup.find('meta', {'itemprop': 'sku'})['content']

        price = Decimal(remove_words(soup.find('span', 'price').text))

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'cloud-zoom')]
        description = html_to_markdown(str(soup.find('div', 'tabs-content')))

        product = Product(
            name,
            cls.__name__,
            'Cell',
            url,
            url,
            sku,
            -1,
            price,
            price,
            'CLP',
            sku=sku,
            cell_plan_name='Claro Prepago',
            description=description,
            picture_urls=picture_urls
        )

        return [product]
