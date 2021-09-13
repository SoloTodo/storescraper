import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CELL_ACCESORY, CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words


class Vivelo(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Tablet',
            'Television',
            'OpticalDiskPlayer',
            'StereoSystem',
            'Refrigerator',
            'WashingMachine',
            'Oven',
            'VacuumCleaner',
            'Monitor',
            'Headphones',
            'Wearable',
            CELL_ACCESORY
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['smartphones/por-modelo/ver-todos.html', 'Cell'],
            ['smartphones/por-modelo/galaxy-a.html', CELL],
            ['smartphones/por-modelo/galaxy-s.html', CELL],
            ['smartphones/por-modelo/galaxy-note.html', CELL],
            ['smartphones/por-modelo/galaxy-fold.html', CELL],
            ['smartphones/accesorios-para-tu-smartphone/ver-todos.html',
             CELL_ACCESORY],
            ['tablets/por-modelo/ver-todos.html', 'Tablet'],
            ['tablets/accesorios-tablet.html', CELL_ACCESORY],
            ['accesorios.html', CELL_ACCESORY],
            ['smartwatches/por-modelo/ver-todos.html', 'Wearable'],
            ['audio/por-tipo/parlantes.html', 'StereoSystem'],
            ['audio/por-tipo/audifonos.html', 'Headphones'],
            ['audio/por-tipo/audifonos-bluetooth.html', 'Headphones'],
            ['smartphones/accesorios-para-tu-smartphone/ver-todos.html',
             'CellAccesory'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.vivelo.cl/{}?limit=all'.format(
                category_path)

            print(category_url)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.findAll('ul', 'products-grid')[-1].findAll(
                'li', 'item')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for link_container in containers:
                product_url = link_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html5lib')

        base_name = soup.find('div', 'product-name').text.strip()
        description = html_to_markdown(
            str(soup.find(
                'div', {'id': 'product_tabs_ficha_tecnica_tabbed_contents'})))

        products = []

        sku_stocks_matches = re.findall(r'({"sku": .+?})', page_source)

        if sku_stocks_matches:
            color_id_to_part_number_and_stock = {}
            for match in sku_stocks_matches:
                json_match = json.loads(match.replace('\t', ''))
                stock = int(json_match['stock'])
                if stock == 1:
                    stock = -1

                color_id_to_part_number_and_stock[json_match['color']] = {
                    'part_number': json_match['sku'].strip()[:50],
                    'stock': stock
                }

            pictures_json = json.loads(re.search(r'({"option_labels":.+)\'',
                                                 page_source).groups()[0])
            product_id_to_picture = pictures_json['base_image']

            pricing_data = json.loads(
                re.search(r'({"attributes":.+)\)', page_source).groups()[0])

            price = Decimal(pricing_data['basePrice'])

            for color_variant in pricing_data['attributes']['173']['options']:
                color_id = color_variant['id']
                color_label = color_variant['label']
                part_number = color_id_to_part_number_and_stock[
                    color_id]['part_number']
                stock = color_id_to_part_number_and_stock[color_id]['stock']

                for product_id in color_variant['products']:
                    sku = product_id
                    if product_id in product_id_to_picture:
                        picture_urls = [product_id_to_picture[product_id]]
                    else:
                        picture_urls = None

                    name = '{} {}'.format(base_name, color_label)

                    p = Product(
                        name,
                        cls.__name__,
                        category,
                        url,
                        url,
                        sku,
                        stock,
                        price,
                        price,
                        'CLP',
                        sku=sku,
                        part_number=part_number,
                        description=description,
                        picture_urls=picture_urls
                    )

                    products.append(p)
        else:
            part_number = soup.find('p', 'sku').find('span').text.strip()
            sku = soup.find('input', {'name': 'product'})['value'].strip()

            price_container = soup.find('span', {'id': 'product-price-' + sku})
            price = Decimal(remove_words(price_container.text))

            if soup.find('div', 'product-shop').find('p', 'out-of-stock'):
                stock = 0
            else:
                stock = -1

            picture_urls = [tag['href'] for tag in
                            soup.findAll('a', 'cloud-zoom-gallery')]

            p = Product(
                base_name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                part_number=part_number,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products
