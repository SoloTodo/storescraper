import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class GearBest(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['/cell-phones-c_11293/c15_asus__c15_huawei__c15_meizu__'
             'c15_oneplus__c15_xiaomi', 'Cell'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            category_base_path = 'https://www.gearbest.com' + category_path

            while True:
                category_url = '{}/{}.html'.format(category_base_path, page)

                if page >= 20:
                    raise Exception('Page overflow: ' + category_url)

                response = session.get(category_url)

                if category_base_path not in response.url:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                link_containers = soup.find(
                    'ul', {'id': 'catePageList'}).findAll('li')

                for link_container in link_containers:
                    if link_container.find('a', 'next-page'):
                        continue
                    product_url = link_container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1').text
        sku = soup.find('meta', {'name': 'GLOBEL:ksku'})['content'].strip()

        description = html_to_markdown(str(soup.find('div', 'detailShow')),
                                       'https://www.gearbest.com')

        picture_tags = soup.find('div', 'n_thumbImg_item').findAll(
            'img', 'js_gbexp_lazy')
        picture_urls = [tag['data-big-img'] for tag in picture_tags]

        if soup.find('a', 'arrivalNoticeBtn') or soup.find(
                'a', 'no_addToCartBtn'):
            stock = 0
            usd_price = Decimal(0)
        else:
            stock_container = soup.find('span', 'num_count_tip')
            if stock_container:
                stock = int(
                    re.search(r'(\d+)', soup.find(
                        'span', 'num_count_tip').text).groups()[0])
            else:
                stock = -1

            price_container = soup.find('span', 'goods_price')

            if not price_container:
                price_container = soup.find('div', 'goods_price')

            if not price_container:
                price_container = soup.find('p', 'goods_price')

            price = price_container.find('b', 'my_shop_price')

            if not price:
                price = price_container.find('span', 'my_shop_price')

            usd_price = Decimal(price['data-orgp'])

        raw_exchange_rates = session.get(
            'https://www.gearbest.com/data-cache/currency_huilv.js').text

        exchange_rates = json.loads(
            re.search(r'my_array=(.+});var my_array_sign',
                      raw_exchange_rates).groups()[0])

        exchange_rate = Decimal(str(exchange_rates['CLP']))

        clp_price = (usd_price * exchange_rate).quantize(0)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            clp_price,
            clp_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
