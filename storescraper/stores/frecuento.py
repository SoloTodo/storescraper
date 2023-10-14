from decimal import Decimal
import json
import logging

from playwright.sync_api import sync_playwright

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown


class Frecuento(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []
        if category != TELEVISION:
            return []

        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(extra_args['pw_proxy'])
            context = browser.new_context()
            session = context.new_page()
            page = 1

            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + category)

                url_webpage = 'https://app.frecuento.com/products-search/?' \
                              'brand_name=LG&stock=true&page={}'.format(page)
                print(url_webpage)
                response = session.goto(url_webpage)
                json_data = json.loads(response.body())['results']

                if len(json_data) == 0:
                    if page == 1:
                        logging.warning('Empty category: ' + category)
                    break

                for r in json_data:
                    url = 'https://www.frecuento.com/{}/{}/'.format(
                        r['slug_name'].replace('”', ''), r['id'])
                    product_urls.append(url)

                page += 1

            context.close()
            browser.close()

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)

        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(extra_args['pw_proxy'])
            context = browser.new_context()
            session = context.new_page()
            key = url.split('/')[-2]
            target_url = 'https://app.frecuento.com/products/{}/?image=455x455'.format(key)
            response = session.goto(target_url)
            json_data = json.loads(response.body())
            context.close()
            browser.close()

        name = json_data['name']
        sku = json_data['code']
        stock = json_data['stock']
        description = html_to_markdown(json_data['description'])
        price = Decimal(json_data['amount_total'])

        picture_urls = json_data['photos']

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
            'USD',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )
        return [p]
