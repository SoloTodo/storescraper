from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION, CELL, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class ClaroEcuador(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
            NOTEBOOK,
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['postpago', CELL],
            ['laptops', NOTEBOOK],
            ['tv', TELEVISION],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://catalogo.claro.com.ec/{}/catalogo'.format(
                url_extension)
            print(url_webpage)

            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div',
                                              'box-wrapper-producto')

            for product in product_containers:
                if 'LG' not in product.find('h3').text:
                    continue

                product_link = product.find('a')
                product_url = 'https://catalogo.claro.com.ec' + \
                              product_link['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        color_selectors = soup.findAll('input', {'name': 'color'})
        key = color_selectors[0]['value']
        assert len(color_selectors) == 1

        name = soup.find('h1').text.strip()
        price = Decimal(soup.find(
            'meta', {'property': 'product:price:amount'})['content'])
        picture_tags = soup.find('div', 'productoGaleriaShow').findAll('img')
        # The page repeats the pictures, no idea why
        picture_tags = picture_tags[:(len(picture_tags) // 2)]
        picture_urls = ['https://catalogo.claro.com.ec/' + tag['data-src']
                        for tag in picture_tags]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            -1,
            price,
            price,
            'USD',
            sku=key,
            picture_urls=picture_urls
        )

        return [p]
