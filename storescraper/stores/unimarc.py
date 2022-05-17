from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import GROCERIES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Unimarc(Store):
    @classmethod
    def categories(cls):
        return [
            GROCERIES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['despensa', GROCERIES]
        ]

        session = session_with_proxy(extra_args)
        products_urls = []
        for url_extension, local_categories in url_extensions:
            if category not in local_categories:
                continue

            page = 1
            while True:
                if page >= 50:
                    raise Exception('Page overflow ' + url_extension)

                url_webpage = 'https://www.unimarc.cl/{}' \
                    '?page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')

                template = soup.find(
                    'template', {'data-varname': '__STATE__'}).text
                if 'linkText' not in template:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                product_data = json.loads(template)
                for item in product_data.values():
                    if 'linkText' in item:
                        products_urls.append(
                            'https://www.unimarc.cl/'
                            + item['linkText'] + '/p')
                page += 1

        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        linkText = url.split('https://www.unimarc.cl/')[-1]
        api_url = 'https://www.unimarc.cl/api/catalog_system/pub/products/' \
            'search/{}'.format(linkText)

        session = session_with_proxy(extra_args)
        response = session.get(api_url)

        json_data = json.loads(response.text)[0]
        key = json_data['productId']
        name = json_data['brand'] + ' - ' + json_data['productName']
        sku = json_data['productReference']
        description = json_data['description']

        item = json_data['items'][0]
        ean = item.get('ean', None)

        picture_urls = []
        for i in item['images']:
            picture_urls.append(i['imageUrl'])

        seller = item['sellers'][0]['commertialOffer']
        price = Decimal(seller['Price'])
        if seller['IsAvailable']:
            stock = int(seller['AvailableQuantity'])
        else:
            stock = 0

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
            'CLP',
            sku=sku,
            ean=ean,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
