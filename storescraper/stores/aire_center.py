import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words,\
    html_to_markdown


class AireCenter(Store):
    @classmethod
    def categories(cls):
        return [
            'AirConditioner',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('aire-acondicionado/split-muro-cool-desing.html',
             'AirConditioner'),
            ('aire-acondicionado/equipo-muro-inverter.html', 'AirConditioner'),
            ('aire-acondicionado/split-muro.html', 'AirConditioner'),
        ]

        product_urls = []

        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.airecenter.cl/index.php/tienda/'\
                           + category_path

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            product_cells = soup.find('div', 'category-view').findAll('a')

            for product_cell in product_cells:
                product_cell_url = 'http://www.airecenter.cl'\
                                   + product_cell['href']
                product_cell_soup = BeautifulSoup(session.get(
                    product_cell_url).text, 'html.parser'
                                                  )
                product_containers = product_cell_soup.findAll(
                    'div', 'product1'
                )

                for product_container in product_containers:
                    product_url = product_container.find('a')['href']
                    product_urls.append(
                        'http://www.airecenter.cl' + product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find("h1", "title").text

        if soup.find("div", "product-price") is None:
            return []

        sku = re.search(r'(\d+)',
                        soup.find("div", "product-price")['id']
                        ).groups()[0]

        stock = -1

        price = soup.find('div', 'product-price')
        price = price.find('div', 'PricesalesPrice').span.text
        price = Decimal(remove_words(price))

        description_a = html_to_markdown(str(soup.find('div', 's_desc').text))
        description_b = html_to_markdown(str(soup.find('div', 'desc')))

        description = description_a + '\n\n' + description_b

        resized_picture_urls = soup.find('ul', 'pagination2').img['src']

        resized_picture_name = resized_picture_urls.split('/')[-1]
        picture_size = re.search(r'(_\d+x\d+)',
                                 resized_picture_name).groups()[0]
        picture_name = resized_picture_name.replace(picture_size, '')

        picture_urls = ['http://www.airecenter.cl/images/stories/'
                        'virtuemart/product/' + picture_name]

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
