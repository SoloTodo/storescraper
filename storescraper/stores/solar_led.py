from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class SolarLed(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightTube',
            'LightProjector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # Ampolletas LED
            ['solarled/5-ampolletas-led', 'Lamp'],
            # ['solarled/6-tubos-led', 'LightTube'],
            # ['solarled/15-focos-led', 'LightProjector'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.solarled.cl/{}?n=200'.format(
                category_path
            )

            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            product_containers = soup.findAll('li', 'ajax_block_product')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', {'id': 'pb-left-column'}).find(
            'h1').text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value'].strip()

        add_to_cart_container = soup.find('p', {'id': 'add_to_cart'})
        if add_to_cart_container.get('style', '') == 'display:none':
            stock = 0
        else:
            stock = -1

        price = Decimal(remove_words(soup.find(
            'span', {'id': 'our_price_display'}).text))

        price = price.quantize(0)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'short_description_content'})))

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'thickbox')]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
