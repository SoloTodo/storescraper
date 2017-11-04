import json
import re
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words


class TiendaMovistar(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Tablet'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('smartphone-liberados.html', 'Cell'),
            ('tablets.html', 'Tablet'),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'https://tienda.movistar.cl/{}?p={}'.format(
                    category_path, page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                items = soup.findAll('li', 'item')

                if not items:
                    raise Exception('No items found for Tienda Movistar')

                done = False

                for cell_item in items:
                    product_url = cell_item.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)

                if done:
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        price_container = soup.find('div', 'price-box').find('span', 'price')
        price = Decimal(remove_words(price_container.text))

        base_name = soup.find('h1', {'itemprop': 'name'}).text.strip()

        description = ''
        for panel_id in ['acctab-description', 'acctab-additional']:
            description += html_to_markdown(
                str(soup.find('div', {'id': panel_id}))) + '\n\n'

        color_data = re.search(r'Product.Config\((.+?)\)',
                               page_source).groups()[0]
        color_data = json.loads(color_data)

        session.headers['x-requested-with'] = 'XMLHttpRequest'

        products = []

        for option in color_data['attributes']['92']['options']:
            color_name = option['label'].strip()
            name = u'{} {}'.format(base_name, color_name)

            product_url = '{}?color={}'.format(url, urllib.parse.quote(
                color_name))

            sku = option['products'][0]

            pictures_ajax_url = 'https://tienda.movistar.cl/amconf/ajax/' \
                                'index/id/{}/'.format(sku)
            color_soup = BeautifulSoup(session.post(pictures_ajax_url).text,
                                       'html.parser')

            picture_urls = [tag['href'] for tag in color_soup.findAll('a')]

            p = Product(
                name,
                cls.__name__,
                category,
                product_url,
                url,
                sku,
                -1,
                price,
                price,
                'CLP',
                sku=sku,
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)

        return products
