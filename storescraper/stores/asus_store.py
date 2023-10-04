import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, ALL_IN_ONE, VIDEO_CARD, MOUSE, \
    VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown


class AsusStore(StoreWithUrlExtensions):
    url_extensions = [
        ('laptops', NOTEBOOK),
        ('displays-desktops', ALL_IN_ONE),
        ('motherboards-components', VIDEO_CARD),
        ('accessories', MOUSE),
        ('mobile-handhelds', VIDEO_GAME_CONSOLE),
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

        product_urls = []
        page = 1

        while True:
            if page >= 10:
                raise Exception('Page overflow')

            url_webpage = 'https://odinapi.asus.com/recent-data/apiv2/' \
                          'ShopAPI/ShopFilterResult?SystemCode=asus&' \
                          'WebsiteCode=cl&ProductLevel1Code={}&' \
                          'PageSize=25&PageIndex={}&Sort=' \
                          'Newsest&siteID=www'.format(url_extension, page)
            print(url_webpage)
            page += 1
            response = session.get(url_webpage).json()
            product_entries = response['Result']['ProductList']
            if not product_entries:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break

            for product_entry in product_entries:
                product_url = product_entry['ProductCardURL']
                product_urls.append(product_url)
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

        for script_tag in soup.findAll('script', {'type': 'text/x-magento-init'}):
            if 'jsonConfig' in script_tag.text:
                variations_data = json.loads(script_tag.text)
                break
        else:
            variations_data = None

        products = []

        if variations_data:
            variations_data = variations_data['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']
            for key, sku in variations_data['sku'].items():
                name = variations_data['sales_model_name'][key]
                price = Decimal(variations_data['optionPrices'][key]['finalPrice']['amount'])
                picture_urls = [x['full'] for x in variations_data['images'][key]]
                description = html_to_markdown(variations_data['dynamic']['short_description'][key]['value'])

                p = Product(
                    name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    -1,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    part_number=sku,
                    picture_urls=picture_urls,
                    description=description
                )
                products.append(p)

        else:
            base_name = soup.find('span', {'data-dynamic': 'product_name'})\
                .text.replace('\u200b', '').strip()
            model_name = soup.find('div', 'simple-sku').text.split(' - ')[-1]\
                .strip()
            name = '{} ({})'.format(base_name, model_name)
            key = soup.find('div', 'price-box')['data-product-id']
            sku = soup.find('div', 'simple-part').text.split(' - ')[-1]
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
                key,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                part_number=sku,
                picture_urls=picture_urls
            )
            products.append(p)
        return products
