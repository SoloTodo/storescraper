import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, \
    session_with_proxy


class Digiplot(Store):
    @classmethod
    def categories(cls):
        return [
            'Monitor',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Monitores
            ['monitor-y-televisor/monitor-led', 'Monitor'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://www.digiplot.cl/product/category/{}'\
                .format(url_extension)

            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', 'product-container')

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        data = json.loads(
            re.search(r'value_product = ([\s\S]+?)\]',
                      response.text).groups()[0] + ']')[0]

        name = data['descripcion'].strip()
        sku = data['idproducto'].strip()
        stock = round(float(data['stock']))
        offer_price = Decimal(data['precioweb1'])
        normal_price = Decimal(data['precioweb2'])
        description = html_to_markdown(data['long_descrip'])
        picture_urls = [x['href'] for x in soup.findAll('a', 'fancybox')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
