import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class HpOnline(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Printer',
            'AllInOne',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['notebooks', 'Notebook'],
            ['impresoras', 'Printer'],
            # ['desktops/desktops-all-in-one', 'AllInOne'],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://store.hp.com/cl-es/default' \
                               '/{}.html?p={}'.format(category_path, page)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')
                product_cells = soup.findAll('div', 'product-item-info')

                if not product_cells:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for cell in product_cells:
                    product_url = cell.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('span', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()
        stock = -1

        price = soup.find('span', {'data-price-type': 'finalPrice'})\
            .find('span', 'price').text.strip()
        price = Decimal(price.replace('$', '').replace('.', ''))

        description = html_to_markdown(str(soup.find(
            'div', 'product info detailed').find('div', 'overview')))

        script_containers = soup.findAll(
            'script', {'type': 'text/x-magento-init'})
        images_json = None

        for script in script_containers:
            if 'data-gallery-role' in script.text:
                images_json = json.loads(script.text)
                break

        picture_urls = []

        if images_json:
            images_data = images_json['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
            for image_data in images_data:
                picture_urls.append(image_data['img'])

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
            part_number=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]