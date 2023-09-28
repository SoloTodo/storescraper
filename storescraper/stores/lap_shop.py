import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, MONITOR, MOUSE, STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class LapShop(StoreWithUrlExtensions):
    url_extensions = [
        ['26-27-29-31', MONITOR],
        ['21', HEADPHONES],
        ['22', STEREO_SYSTEM],
        ['33', MOUSE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow')
            url_webpage = ('https://lapshop.cl/page/{}/?post_type=product&'
                           'filters=product_cat[{}]').format(
                page, url_extension)
            print(url_webpage)
            res = session.get(url_webpage)
            soup = BeautifulSoup(res.text, 'html.parser')
            product_containers = soup.findAll('li', 'product')

            if not product_containers:
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
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        json_data = json.loads(soup.find(
            'script', {'type': 'application/ld+json'}).text)
        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        name = product_data['name']
        sku = product_data['sku']

        input_qty = soup.find('input', 'qty')
        if input_qty:
            if 'max' in input_qty.attrs and input_qty['max']:
                stock = int(input_qty['max'])
            else:
                stock = -1
        else:
            stock = 0

        summary_tag = soup.find('div', 'entry-summary')
        price_tags = summary_tag.findAll('span', 'woocommerce-Price-amount')
        assert len(price_tags) in [2, 3]

        offer_price = Decimal(remove_words(price_tags[0].text))
        normal_price = Decimal(remove_words(price_tags[-1].text))

        if 'SEGUNDA' in name.upper():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        picture_urls = [x['href'] for x in soup.findAll(
            'a', {'data-fancybox': 'product-gallery'})]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            condition=condition
        )
        return [p]
