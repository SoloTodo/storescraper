from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION, STEREO_SYSTEM, CELL, \
    REFRIGERATOR, OVEN, AIR_CONDITIONER, WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Tecnofacil(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page >= 25:
                    raise Exception('Page overflow')

                url = 'https://www.tecnofacil.com.gt/catalogsearch/result' \
                      '/index/?limit=30&marca=7&p={}&q=LG'.format(page)
                print(url)
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'col-sm-6')

                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in product_urls:
                        return product_urls
                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')
        sku_container = soup.find('h6', 'sku')

        if not sku_container:
            return []

        sku = sku_container.text.strip()
        name = "{} ({})".format(soup.find('div', 'product-name')
                                .find('h1').text.strip(), sku)
        if soup.find('p', 'availability') and soup.find('p',
                                                        'availability').find(
            'span').text == '✔' or soup.find('div',
                                             'availability-in-store'):
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('div', 'price-box').find('span', 'price')
                        .text.replace('Q', '').replace(',', ''))

        picture_urls = [soup.find('p', 'product-image').find('a')['href']]
        description = html_to_markdown(str(
            soup.find('div', {'id': 'product_tabs_description_contents'})))

        description += '\n\n'

        description += html_to_markdown(str(
            soup.find('div', {'id': 'product_tabs_additional_contents'})))

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
            'GTQ',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
