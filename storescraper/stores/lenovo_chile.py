from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy

import json


class LenovoChile(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        nb_path = "products/json?categoryCodes=thinkpadx%2Cthinkpadt%2" \
                  "Cthinkpade%2Cthinkpadp%2Cthinkpadyoga%2Clegion-y-series%2" \
                  "Cyoga-c-series%2Cyoga-s-series%2Cyoga-500-series%2" \
                  "Cyoga-300-series%2CIdeaPad-100%2CIdeaPad-300%2" \
                  "CIdeaPad-500%2Cww-ideapad-s-series-redesign%2Cv-series%2" \
                  "Clenovo-g-series%2Clenovo-serie-y"

        session = session_with_proxy(extra_args)
        products_urls = []

        if category != 'Notebook':
            return []

        url = 'https://www.lenovo.com/cl/es/c/{}'.format(nb_path)
        products_json = json.loads(session.get(url).text)

        for key in products_json:
            series = products_json[key]
            for product in series:
                products_urls.append('https://www.lenovo.com/cl/es{}'
                                     .format(product['url']))

        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        models_containers = soup.findAll('div', 'tabbedBrowse-productListing')
        products = []

        if models_containers:
            for model_container in models_containers:
                name = model_container\
                    .find('h3', 'tabbedBrowse-productListing-title')\
                    .contents[0].strip()
                sku = model_container.find('div', 'partNumber').text\
                    .replace('Modelo:', '').strip()

                price = model_container\
                    .find('dd', 'pricingSummary-details-final-price').text\
                    .replace('.', '').replace('$', '').replace(',', '.')

                price = Decimal(price)

                description = html_to_markdown(str(
                    model_container
                    .find('div', 'tabbedBrowse-productListing-featureList')))

                picture_urls = ['https://www.lenovo.com' +
                                soup.find('img', 'subSeries-Hero')['src']]

                stock_msg = model_container.find('span', 'stock_message').text

                if stock_msg == 'Agotado':
                    stock = 0
                else:
                    stock = -1

                products.append(Product(
                    '{} ({})'.format(name, sku),
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
                ))

        elif soup.find('div', 'singleModelView'):
            name = soup.find('h2', 'tabbedBrowse-title singleModelTitle')\
                .text.strip()
            sku = soup.find('div', 'partNumber').text\
                .replace('Modelo:', '').strip()

            price_tag = soup.find('meta', {'name': 'productsaleprice'})

            if not price_tag:
                price_tag = soup.find('meta', {'name': 'productprice'})

            if not price_tag:
                price = Decimal(remove_words(
                    soup.find('dd',
                              'saleprice pricingSummary-details-final-price')
                        .text.split(',')[0]))
            else:
                price = Decimal(remove_words(price_tag['content']
                                             .split(',')[0]))

            description = html_to_markdown(str(soup.find(
                'div', 'configuratorItem-accordion-content')))

            picture_urls = ['https://www.lenovo.com' +
                            soup.find('img', 'subSeries-Hero')['src']]

            stock_msg = soup.find('span', 'stock_message').text
            stock = -1

            if stock_msg == 'Agotado':
                stock = 0

            p = Product(
                '{} ({})'.format(name, sku),
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

            products.append(p)

        return products
