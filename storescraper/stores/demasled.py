from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Demasled(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightTube'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'https://www.dled.cl'

        category_paths = [
            # Ampolletas LED
            ['/bipin-mr16', 'Lamp'],
            ['/dicroicas-gu10', 'Lamp'],
            # ['/ampolletas-g9', 'Lamp'],
            ['/rosca-e27-ampolleta-tradicional', 'Lamp'],
            ['/ampolleta-par', 'Lamp'],
            # Tubos LED
            ['/tubo-60cm', 'LightTube'],
            ['/tubo-120cm', 'LightTube'],
            ['/tubo-150cm', 'LightTube'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = url_base + category_path

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            product_containers = soup.findAll('li', 'ajax_block_product')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for container in product_containers:
                product_url = url_base + container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).content, 'html.parser')

        name = soup.find('h1').text.strip()
        sku = soup.find('div', 'codigo-producto').text.split(':')[1].strip()

        if soup.find('a', 'btnAddBasketHome'):
            stock = -1
        else:
            stock = 0

        price = Decimal(remove_words(soup.find(
            'div', 'precio').find('label').string))

        price *= Decimal('1.19')
        price = price.quantize(0)

        panels = soup.findAll('section', 'page_product_box')

        description = '\n\n'.join(
            [html_to_markdown(str(panel), 'https://www.dled.cl')
             for panel in panels])

        picture_urls = ['https://www.dled.cl' + tag['href']
                        for tag in soup.findAll('a', 'cloud-zoom-gallery')]

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
