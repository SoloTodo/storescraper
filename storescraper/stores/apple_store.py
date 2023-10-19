import re
from decimal import Decimal
import json
from bs4 import BeautifulSoup
from storescraper.categories import CELL, NOTEBOOK, TABLET, WEARABLE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class AppleStore(StoreWithUrlExtensions):
    url_extensions = [
        ['buy-iphone', CELL],
        ['buy-mac', NOTEBOOK],
        ['buy-ipad', TABLET],
        ['buy-watch', WEARABLE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        url = 'https://www.apple.com/cl/shop/{}'.format(url_extension)
        response = session.get(url)
        match = re.search(r'cards: (.+)', response.text)
        page_data = json.loads(match.groups()[0])
        for item in page_data['items']:
            card_type = item['value']['items'][0]['value']['cardType']
            if 'heroCard' not in card_type:
                continue
            url = card_type['heroCard']['heroStoreCard']['title']['link']
            if not isinstance(url, str):
                url = url['url']
            if not url.startswith('https'):
                url = 'https://www.apple.com' + url
            product_urls.append(url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        product_match = re.search(r'productSelectionData: (.+)', response.text)
        products = []

        if product_match:
            product_data = json.loads(product_match.groups()[0])
            for product_entry in product_data['products']:
                dimensions = []
                if 'partNumber' in product_entry:
                    mpn = product_entry['partNumber']
                    for key, value in product_entry.items():
                        if key.startswith('dimension') and isinstance(value,
                                                                      str):
                            dimensions.append(value)
                    name = '{} ({})'.format(product_entry['familyType'],
                                            ' / '.join(dimensions))
                else:
                    mpn = product_entry['part']

                    for key, value in product_entry['dimensions'].items():
                        label = key.replace('watch_cases-dimension', '')
                        dimensions.append('{} {}'.format(label, value))

                    name = '{} ({})'.format(mpn, ' / '.join(dimensions))

                if 'fullPrice' in product_entry:
                    price = Decimal(
                        product_data['displayValues']['prices'][product_entry['fullPrice']]['amountBeforeTradeIn'])
                elif 'price' in product_entry:
                    price = Decimal(
                        product_data['displayValues']['prices'][
                            product_entry['price']]['currentPrice']['raw_amount']).quantize(0)
                else:
                    price = Decimal(
                        product_data['displayValues']['prices'][
                            product_entry['priceKey']]['currentPrice'][
                            'raw_amount']).quantize(0)

                p = Product(
                    name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    mpn,
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=mpn,
                    part_number=mpn
                )
                products.append(p)
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            noscript_tag = soup.findAll('noscript')[1]
            for form_tag in noscript_tag.findAll('form'):
                product_id = form_tag.find('input', {'name': 'product'})['value']
                tckey_tag = form_tag.find('input', {'name': 'tckey'})
                if tckey_tag:
                    tckey = tckey_tag['value']
                else:
                    tckey = ''
                sku_url = '{}?product={}&tckey={}&proceed=proceed'.format(url, product_id, tckey)
                response = session.get(sku_url)
                product_url = response.url
                product_data = json.loads(re.search(r'initData:(.+)', response.text).groups()[0])
                name = product_data['content']['summary']['productName']
                mpn = product_data['content']['creditMessage']['price']['partNumber']
                price = Decimal(product_data['content']['creditMessage']['price']['taxInclusivePrice']).quantize(0)
                p = Product(
                    '{} ({})'.format(name, mpn),
                    cls.__name__,
                    category,
                    url,
                    product_url,
                    mpn,
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=mpn,
                    part_number=mpn
                )
                products.append(p)
        return products
