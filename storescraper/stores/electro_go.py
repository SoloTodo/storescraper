from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, \
    session_with_proxy


class ElectroGo(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        url_webpage = 'https://credivargas.pe/tienda/pucallpa/m/lg'
        print(url_webpage)
        data = session.get(url_webpage).text
        soup = BeautifulSoup(data, 'html.parser')
        product_containers = soup.findAll('h5', 'product-item__title')
        if not product_containers:
            logging.warning('Empty category')
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

        key = url.split('-')[-1]
        name = soup.find('h2', 'text-lh-1dot2').text.strip()
        stock = int(
            soup.find('span', 'text-green').text.replace(' en stock', ''))

        product_info = soup.find('div', 'col-wd-9gdot5').find('div', 'mb-lg-0')
        sku = product_info.findAll('p')[-1].text.split(':')[-1].strip()

        price_div = product_info.find('ins', 'text-decoration-none')
        if not price_div:
            return []

        price = Decimal(remove_words(price_div.text, ['S/.', ',']))
        description = html_to_markdown(product_info.find('h2').text)

        picture_urls = []
        picture_container = soup.find('div', {'id': 'sliderSyncingNav'})
        for i in picture_container.findAll('img'):
            picture_urls.append(i['src'].replace(' ', '%20'))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'PEN',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
