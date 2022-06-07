import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class AsusStore(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            ALL_IN_ONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Products URL: https://www.asus.com/cl/deals/All-Deals/
        url_extensions = [
            ['Laptops', 99, NOTEBOOK],
            ['Displays-Desktops', 197, ALL_IN_ONE]
        ]
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []
        for url_extension, category_id, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://odinapi.asus.com/apiv2/DealsFilter' \
                              'Result?SystemCode=asus&WebsiteCode=cl&' \
                              'ProductLevel1Code={}&DealsLevelID={}&Type=2' \
                              '&PageSize=20&PageIndex={}&' \
                              'Sort=Newsest&siteID=www'.format(url_extension,
                                                               category_id,
                                                               page)
                print(url_webpage)
                response = session.get(url_webpage)
                product_containers = json.loads(response.text)['Result'][
                    'ProductList']
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container['Buy']['Link'].strip()
                    if not product_url:
                        continue
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        try:
            response = session.get(url, timeout=30)
        except Exception as e:
            return []

        if response.status_code == 401:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        base_name = soup.find('span', {'data-dynamic': 'product_name'})\
            .text.replace('\u200b', '').strip()
        model_name = soup.find('div', 'simple-sku').text.split(' - ')[-1]\
            .strip()
        name = '{} ({})'.format(base_name, model_name)
        sku = soup.find('div', 'price-box')['data-product-id']
        part_number = soup.find('div', 'simple-part').text.split(' - ')[-1]
        if soup.find('div', 'box-tocart').find('div', 'out-stock'):
            stock = 0
        else:
            stock = -1
        price = Decimal(soup.find('span', {'data-price-type': 'finalPrice'})[
                            'data-price-amount'])
        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'product media').findAll('img')]
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
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
