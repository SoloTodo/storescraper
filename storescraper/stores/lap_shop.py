import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MONITOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class LapShop(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            MONITOR
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow')
                url_webpage = 'https://www.lapshop.cl/collections/all?' \
                              'page={}'.format(page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'grid-uniform').findAll(
                    'a', 'product-grid-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty Category')
                    break
                for container in product_containers:
                    product_url = container['href']
                    product_urls.append('https://www.lapshop.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_info = json.loads(
            soup.find('script', {'id': 'ProductJson-product-template'}).text)
        name = json_info['title']
        sku = str(json_info['id'])
        stock = -1 if json_info['available'] else 0
        normal_price = Decimal(json_info['price'] // 100)
        offer_price = (normal_price * Decimal('0.96')).quantize(0)
        picture_urls = ['https:' + image_url.split('?')[0] for image_url in
                        json_info['images']]

        if 'SEGUNDA' in name.upper():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

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
            picture_urls=picture_urls,
            condition=condition
        )
        return [p]
