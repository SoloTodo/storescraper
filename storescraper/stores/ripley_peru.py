import json

import time
from decimal import Decimal

import validators
from playwright.sync_api import sync_playwright
from ..categories import TELEVISION
from ..product import Product
from ..store import Store
from ..utils import session_with_proxy


class RipleyPeru(Store):
    # Only returns LG products
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        time.sleep(3)

        if category != TELEVISION:
            return []

        return [TELEVISION]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(extra_args)
        session = session_with_proxy(extra_args)
        session.headers = extra_args['headers']
        for cookie in extra_args['cookies']:
            cookie['rest'] = {}
            if 'sameSite' in cookie:
                cookie['rest']['sameSite'] = cookie.pop('sameSite')
            if 'httpOnly' in cookie:
                cookie['rest']['httpOnly'] = cookie.pop('httpOnly')
            session.cookies.set(**cookie)

        products = []
        page = 1

        while True:
            if page > 100:
                raise Exception('Page overflow')

            print(page)

            payload = {
                'filters': [
                    {
                        'type': 'brands',
                        'value': 'LG',
                        'key': 'brand.keyword'
                    }
                ],
                'term': 'lg lg',
                'perpage': 50,
                'page': page,
                'sort': 'score'
            }
            print(json.dumps(payload))
            response = session.post(
                'https://simple.ripley.com.pe/api/v2/search', json=payload)
            json_data = response.json()

            if 'products' not in json_data:
                if page == 1:
                    raise Exception('Empty site')
                break

            products_data = json_data['products']

            for product_entry in products_data:
                name = product_entry['name']
                sku_entry = product_entry['SKUs'][0]
                sku = sku_entry['partNumber']

                seller_id = product_entry['sellerOp']['seller_id']
                if seller_id == 1:
                    seller = None
                else:
                    seller = product_entry['sellerOp']['shop_name']

                if seller:
                    stock = 0
                elif product_entry['buyable']:
                    stock = -1
                else:
                    stock = 0

                normal_price = Decimal(
                    sku_entry['prices']['offerPrice']
                ).quantize(Decimal('0.01'))

                if 'cardPrice' in sku_entry['prices']:
                    offer_price = Decimal(
                        sku_entry['prices']['cardPrice']
                    ).quantize(Decimal('0.01'))
                else:
                    offer_price = normal_price

                if offer_price > normal_price:
                    offer_price = normal_price

                picture_urls = []
                for x in product_entry['images']:
                    if x.startswith('http'):
                        picture_url = x
                    else:
                        picture_url = 'https:' + x

                    if validators.url(picture_url):
                        picture_urls.append(picture_url)

                p = Product(
                    name,
                    cls.__name__,
                    category,
                    product_entry['url'],
                    url,
                    sku,
                    stock,
                    normal_price,
                    offer_price,
                    'PEN',
                    sku=sku,
                    picture_urls=picture_urls,
                    seller=seller,
                )

                products.append(p)
            page += 1

        return products

    @classmethod
    def preflight(cls, extra_args=None):
        if not extra_args or 'pw_proxy' not in extra_args:
            raise Exception('Playwright proxy args is required')

        with sync_playwright() as pw:
            print('connecting')
            browser = pw.chromium.connect_over_cdp(extra_args['pw_proxy'])
            context = browser.new_context()
            print('connected')
            page = context.new_page()
            print('goto')
            response = page.goto('https://simple.ripley.com.pe/',
                                 timeout=120000)
            headers = response.request.headers
            cookies = context.cookies()
            context.close()
            browser.close()

        return {
            'cookies': cookies,
            'headers': headers
        }
