import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13, remove_words


class LinioChile(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Cell',
            'Television',
            'Tablet',
            'Printer',
            'VideoGameConsole',
            'Refrigerator',
            'WashingMachine',
            'Oven',
            'VacuumCleaner',
            'ExternalStorageDrive',
            'Keyboard',
            'Mouse',
            'AllInOne',
            'Monitor',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['computacion/pc-portatil', 'Notebook'],
            # ['zona-gamer/notebook-gamer', 'Notebook'],
            ['celulares-y-smartphones/liberados', 'Cell'],
            ['tv-y-video/televisores/', 'Television'],
            # ['tv-audio-y-foto/', 'Television'],
            ['tablets/tablet', 'Tablet'],
            ['impresoras-y-scanners/impresoras', 'Printer'],
            ['impresoras/impresoras-laser', 'Printer'],
            ['impresoras-y-scanners/multifuncionales', 'Printer'],
            ['nintendo-videojuegos/consolas-nintendo/', 'VideoGameConsole'],
            ['playstation-videojuegos/consolas-playstation/',
             'VideoGameConsole'],
            ['xbox-videojuegos/consolas-xbox/', 'VideoGameConsole'],
            ['refrigeracion/refrigeradores/', 'Refrigerator'],
            ['lavado-y-secado/lavadoras/', 'WashingMachine'],
            ['lavado-y-secado/secadoras/', 'WashingMachine'],
            ['pequenos-electrodomesticos/microondas-y-hornos/', 'Oven'],
            ['pequenos-electrodomesticos/aspiradoras/', 'VacuumCleaner'],
            ['discos-duros/discos-duros-externos/', 'ExternalStorageDrive'],
            # ['tabletas-digitalizadoras/teclados-pc/', 'Keyboard'],
            ['mouse-kit/mouse/', 'Mouse'],
            ['pc-escritorio/all-in-one/', 'AllInOne'],
            ['pc-escritorio/monitores/', 'Monitor'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        sortings = ['relevance', 'price_asc', 'price_desc']

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            for sorting in sortings:
                page = 1

                while True:
                    category_url = 'https://www.linio.cl/c/{}?sortBy={}&page' \
                                   '={}'.format(category_path, sorting, page)
                    if page >= 40:
                        raise Exception('Page overflow: ' + category_url)

                    soup = BeautifulSoup(session.get(category_url).text,
                                         'html.parser')

                    products_containers = \
                        soup.findAll('div', 'catalogue-product')

                    if not products_containers:
                        if page == 1:
                            raise Exception('Empty category: ' + category_url)
                        break

                    for product_container in products_containers:
                        if product_container.find(
                                'div', 'badge-international-shipping'):
                            continue

                        product_url = 'https://www.linio.cl' + \
                                      product_container.find('a')['href']

                        product_url = product_url.split('?')[0]
                        product_urls.append(product_url)

                    page += 1

        return list(set(product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404 or response.url != url:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        key = re.search(r'-([a-zA-Z0-9]+)$', url).groups()[0]
        page_source = response.text
        pricing_str = re.search(r'dataLayer = ([\S\s]+?);\n',
                                page_source).groups()[0]
        pricing_data = json.loads(pricing_str)[0]

        name = pricing_data['product_name']
        sku = pricing_data['sku_config']

        reference_code = pricing_data['ean_code'].strip()
        ean = None

        if check_ean13(reference_code):
            ean = reference_code
        else:
            name = '{} - {}'.format(name, reference_code)

        normal_price = Decimal(pricing_data['special_price'])

        pricing_container = soup.find('div', 'product-price-lg')

        if not soup.find('span', 'sprite-cmr'):
            offer_price = normal_price
        else:
            offer_price_container = pricing_container.find(
                'span', 'price-promotional')

            if offer_price_container:
                offer_price = Decimal(remove_words(offer_price_container.text))
                if offer_price > normal_price:
                    offer_price = normal_price
            else:
                offer_price = normal_price

        soup = BeautifulSoup(page_source, 'html.parser')

        condition_dict = {
            'Nuevo': 'https://schema.org/NewCondition',
            'Reacondicionado': 'https://schema.org/RefurbishedCondition',
        }

        condition_label = soup.find('span', 'badge-condition-type')

        if condition_label:
            condition = condition_dict[condition_label.text.strip()]
        else:
            condition = 'https://schema.org/NewCondition'

        description = html_to_markdown(
            str(soup.find('div', 'feature-information')))

        description += '\n\n' + html_to_markdown(
            str(soup.find('div', 'features-box-section')))

        picture_urls = ['https:' + tag.find('img')['data-lazy'] for tag in
                        soup.findAll('div', {'id': 'image-product'})]

        availability_container = soup.find('link',
                                           {'itemprop': 'availability'})

        if not availability_container:
            stock = 0
        elif soup.find('div', 'feature-information').find(
                'span', 'badge-pill-international-shipping'):
            stock = 0
            description = 'ST-INTERNATIONAL-SHIPPING {}'.format(description)
        elif availability_container['href'] == 'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

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
            ean=ean,
            description=description,
            picture_urls=picture_urls,
            condition=condition
        )

        return [p]
