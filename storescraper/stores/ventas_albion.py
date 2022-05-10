import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class VentasAlbion(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow')
                url_webpage = 'https://ventasalbion.com/tienda/page/{}/?' \
                              'filter_marca=lg&per_page=32' \
                              '&_pjax=.main-page-wrapper' \
                              '&loop=32&woo_ajax=1'.format(page)
                print(url_webpage)

                data = session.get(url_webpage)
                if data.status_code == 404:
                    break
                soup = BeautifulSoup(json.loads(data.text)['items'],
                                     'html.parser')
                product_containers = soup.findAll('div', 'product-grid-item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category')
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        base_name = soup.find('h1', 'product_title').text
        variations_form = soup.find('form', 'variations_form')
        products = []

        if variations_form:
            variation_entries = json.loads(
                variations_form['data-product_variations'])
            for variation_entry in variation_entries:
                name = '{} ({})'.format(
                    base_name,
                    variation_entry['attributes']['attribute_pa_color'])
                key = str(variation_entry['variation_id'])

                # stock_text is a number or ''
                stock_text = variation_entry['max_qty']
                if stock_text:
                    stock = stock_text
                else:
                    stock = 0

                price = Decimal(variation_entry['display_price'])
                picture_urls = [x['src'] for x in
                                variation_entry[
                                    'additional_variation_images_default']]
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
                    sku=key,
                    picture_urls=picture_urls
                )
                products.append(p)

        else:
            product_data = json.loads(
                soup.find('script', {'type': 'application/ld+json'}).text)
            key = str(product_data['sku'])
            stock_tag = soup.find('input', {'name': 'quantity'})
            stock = 0
            if stock_tag:
                if 'max' in stock_tag.attrs and stock_tag['max']:
                    stock = int(stock_tag['max'])
                else:
                    stock = -1
            price = Decimal(product_data['offers'][0]['price'])
            picture_urls = [tag['src'] for tag in soup.find(
                'div', 'woocommerce-product-gallery').findAll('img')]

            p = Product(
                base_name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                price,
                price,
                'USD',
                sku=key,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
