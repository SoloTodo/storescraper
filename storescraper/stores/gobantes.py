from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Gobantes(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightProjector'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Ampolletas LED
            ['iluminacion/lamparas-led', 'Lamp'],
            # Proyectores LED
            ['iluminacion/proyectores-led', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.gobantes.cl/{}?limit=200'.format(
                category_path
            )

            soup = BeautifulSoup(session.get(category_url, verify=False).text,
                                 'html.parser')

            product_containers = soup.findAll('div', 'image')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = container.find('a')['href'].replace(
                    '&limit=200', '').replace('https://gobantes.cl/',
                                              'https://www.gobantes.cl/')
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url, verify=False).text,
                             'html.parser')

        model = soup.find('h1').text.strip()
        brand = soup.find('span', text='Marca:')

        if brand:
            brand = brand.next.next.next.text.strip()
            name = '{} {}'.format(brand, model)
        else:
            name = model

        sku = soup.find('span', text='SKU:').next.next.strip()

        description = html_to_markdown(str(soup.find(
            'div', {'id': 'tab-description'})))

        picture_urls = [tag['href'].replace(' ', '%20') for tag in
                        soup.findAll('a', 'colorbox')]

        price = Decimal(remove_words(soup.find(
            'div', 'price').text.split(':')[1]))

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
