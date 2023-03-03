import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MONITOR, MOUSE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class LapShop(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
            HEADPHONES,
            MOUSE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['monitores-gamer', MONITOR],
            ['monitores-business', MONITOR],
            ['audio', HEADPHONES],
            ['teclados-y-mouse', MOUSE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow')
                url_webpage = 'https://www.lapshop.cl/collections/{}?' \
                              'page={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_container = soup.find('ul', 'productgrid--items')
                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_container.findAll(
                        'a', 'productitem--image-link'):
                    product_url = container['href']
                    product_urls.append('https://www.lapshop.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_info = json.loads(
            soup.find('script', {'data-section-type': 'static-product'}).text
        )['product']
        name = json_info['title']
        sku = str(json_info['id'])
        stock = -1 if json_info['available'] else 0
        normal_price = Decimal(json_info['price'] // 100)
        prices = soup.find('div', 'product-block--price')
        offer_price = Decimal(remove_words(
            prices.find('span', 'money').text))
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
