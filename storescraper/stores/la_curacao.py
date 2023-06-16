from decimal import Decimal
import json
import logging
import re
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class LaCuracao(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        url_webpage = 'https://www.lacuracao.pe/webapp/wcs/stores/se' \
            'rvlet/CategoryNavigationResultsGridScrollView?categoryI' \
            'd=3074457345616720688&storeId=10151&pageSize=1000'
        print(url_webpage)
        data = session.get(url_webpage).text
        soup = BeautifulSoup(data, 'html.parser')
        product_containers = soup.findAll('div', 'product')
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

        if soup.find('div', 'error-lc-404'):
            return []

        key = re.search(r'id="ProductInfoName_(\d*)"',
                        response.text).groups()[0].split('_')[-1]

        name = soup.find('input', {'id': f'ProductInfoName_{key}'})[
            'value'].strip()
        sku = soup.find('span', {'id': f'product_SKU_{key}'}).text.split(
            'SKU:')[-1].strip()
        price = Decimal(str(soup.find(
            'input', {'id': f'ProductInfoPrice_{key}'}
        )['value']).replace(",", ""))

        page_id = soup.find('meta', {'name': 'pageId'})['content']
        stock_tag = soup.find('div', {'id': 'entitledItem_' + page_id})
        json_stock = json.loads(stock_tag.text)[0]
        if json_stock['buyable'] == 'true':
            stock = -1
        else:
            stock = 0

        pictures_data = soup.find(
            'div', {'id': 'ProductAngleProdImagesAreaProdList'})
        if pictures_data:
            picture_urls = ['https://www.lacuracao.pe' + tag['src'].replace(
                '200x310', '646x1000') for tag in pictures_data.findAll('img')]
        else:
            picture_urls = []

        description = html_to_markdown(
            soup.find('div', {'id': f'product_longdescription_{key}'}).text)

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
            'PEN',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
