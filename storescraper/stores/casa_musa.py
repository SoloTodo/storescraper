from _decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class CasaMusa(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightTube'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Ampolletas LED
            ['led/ampolletas-led.html', 'Lamp'],
            # Tubos LED
            ['led/tubos-led.html', 'LightTube'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue
            category_url = 'https://www.casamusa.cl/iluminacion/{}' \
                           '?limit=36'.format(category_path)
            soup = BeautifulSoup(session.get(category_url, verify=False).text,
                                 'html.parser')

            containers = soup.findAll('div', 'product-block')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url, verify=False).text,
                             'html.parser')

        name = soup.find('h1').text.strip()
        pricing_container = soup.find('div', 'wrap-product-shop')

        sku = pricing_container.find('p').text.split(':')[1].strip()

        price = Decimal(remove_words(
            pricing_container.find(
                'p', 'special-price').find('span', 'price').contents[0]))

        price *= Decimal('1.19')
        normal_price = price.quantize(0)
        offer_price = normal_price

        description_ids = ['tab-descripcion', 'tab-adicional',
                           'tab-ficha_tecnica']

        descriptions = []
        for descrption_id in description_ids:
            tag = soup.find('div', {'id': descrption_id})
            if tag:
                descriptions.append(html_to_markdown(str(tag)))

        description = '\n\n'.join(descriptions)

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'colorbox')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
