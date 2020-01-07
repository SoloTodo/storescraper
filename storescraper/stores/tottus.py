import re

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Tottus(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'Cell',
            'Tablet',
            'StereoSystem',
            'Headphones',
            'VideoGameConsole',
            'Printer',
            'Refrigerator',
            'WashingMachine',
            'Notebook',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        url_base = 'http://www.tottus.cl'

        category_paths = [
            ['Televisores/cat2290025', ['Television'],
             'Televisores', 1],
            ['Televisores/cat2290025',
             ['Television'],
             'Televisores', 1],
            ['Smartphones/cat2290023', ['Cell'],
             'Smartphones', 1],
            ['Celulares/cat2280074', ['Cell', 'Tablet'],
             'Celulares', 0],
            ['Freezer-y-Refrigerador/cat2130070', ['Refrigerator'],
             'Freezer y Refrigerador', 1],
            ['Lavadora/cat2130072', ['WashingMachine'],
             'Lavadora', 1],
            ['Audio/cat2280075', ['StereoSystem'],
             'Audio', 1],
            ['NoteBook-y-PC/cat660015', ['Notebook'], 'NoteBook y PC', 1],
            # ['Consolas-y-Videojuegos/cat2290026', ['VideoGameConsole'],
            #  'Consolas y Videojuegos', 1],
        ]

        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            category_url = '{}/tottus/browse/{}'.format(url_base,
                                                        category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            product_containers = soup.findAll(
                'div', 'item-product-caption')

            if not product_containers:
                raise Exception('Empty category: ' + category_url)

            for idx, container in enumerate(product_containers):
                product_url = container.findAll('a')[3]['href'].split('?')[0]
                product_url = '{}{}'.format(url_base, product_url)

                product_entries[product_url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'title').find('h5').text.strip()
        sku = soup.find('input', {
            'name': '/atg/commerce/order/purchase/CartModifierFormHandler.'
                    'items[0].productId'})['value'].strip()

        if len(soup.findAll('div', 'out-of-stock')) == 2:
            stock = 0
        else:
            stock = -1

        if soup.find('div', 'offer-imbatible'):
            prices_raw_text = soup.find(
                'div', 'active-offer').find('span', 'red').text

            prices_array = re.findall(r'([\d.]+)', prices_raw_text)
            offer_price_text = prices_array[0]

            if len(prices_array) > 1:
                normal_price_text = prices_array[1]
            else:
                normal_price_text = offer_price_text

            normal_price = Decimal(remove_words(normal_price_text))
            offer_price = Decimal(remove_words(offer_price_text))

            if offer_price > normal_price:
                offer_price = normal_price
        else:
            prices_container = soup.find('div', 'price-selector')

            offer_price_container = prices_container.find('span', 'red')

            if offer_price_container:
                price = Decimal(remove_words(
                    offer_price_container.text
                ))
            else:
                price = Decimal(remove_words(
                    prices_container.find(
                        'span', 'active-price').find('span').text
                ))

            normal_price = offer_price = price

        description = html_to_markdown(str(soup.find('div', {'id': 'tab_1'})))

        picture_urls = ['http://s7d2.scene7.com/is/image/Tottus/{}?scl=1.0'
                        ''.format(sku)]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]
