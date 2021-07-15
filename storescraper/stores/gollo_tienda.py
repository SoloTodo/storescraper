from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown

import json


class GolloTienda(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # KEEPS ONLY LG PRODUCTS
        session = session_with_proxy(extra_args)
        product_urls = []

        if category != TELEVISION:
            return []

        url = 'https://www.gollotienda.com/productos?at_marca=LG&' \
              'product_list_limit=100'

        print(url)

        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', 'products')
        items = container.findAll('li', 'item')

        for item in items:
            product_url = item.find('a')['href']
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        data = response.text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('span', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()

        if soup.find('div', 'stock available')\
                .find('span').text == "Disponible":
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('span', {'data-price-type': 'finalPrice'})[
                            'data-price-amount'])

        description = html_to_markdown(
            str(soup.find('div', 'additional-attributes-wrapper')))

        description += '\n\n{}'.format(html_to_markdown(
            str(soup.find('div', 'product attribute description'))
        ))

        description += '\n\n{}'.format(html_to_markdown(
            str(soup.find('div', 'dimensions-wrapper'))
        ))

        scripts = soup.findAll('script', {'type': 'text/x-magento-init'})
        img_json_data = None

        for script in scripts:
            if 'mage/gallery/gallery' in script.text:
                img_json_data = json.loads(script.text)[
                    '[data-gallery-role=gallery-placeholder]'][
                    'mage/gallery/gallery']['data']
                break

        if not img_json_data:
            picture_urls = None
        else:
            picture_urls = [image['full'] for image in img_json_data]

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
            'CRC',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
