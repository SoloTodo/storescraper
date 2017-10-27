from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class ImpDali(Store):
    @classmethod
    def categories(cls):
        return [
            'LightTube',
            'LightProjector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1

        while True:
            category_url = 'http://www.impdali.cl/iluminacion-led/page/{}/' \
                           ''.format(page)

            if page >= 10:
                raise Exception('Page overflow:' + category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            containers = soup.findAll('div', 'default_product_display')

            if not containers:
                break

            for container in containers:
                product_link = container.find('a', 'wpsc_product_title')

                product_name = product_link.text.lower()

                ptype = None

                if 'tubo' in product_name:
                    ptype = 'LightTube'
                elif 'proyector' in product_name:
                    ptype = 'LightProjector'

                if ptype == category:
                    product_url = product_link['href']
                    product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'entry-title').text.strip()
        sku = soup.find('input', {'name': 'product_id'})['value'].strip()
        description = html_to_markdown(
            str(soup.find('div', 'product_description')))
        picture_urls = [tag['href'] for tag in soup.findAll('a', 'thickbox')]
        price = Decimal(remove_words(soup.find('span', 'currentprice').text))

        price *= Decimal('1.19')
        price = price.quantize(0)

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
