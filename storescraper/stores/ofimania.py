import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import SOLID_STATE_DRIVE, HEADPHONES, KEYBOARD, \
    NOTEBOOK, TABLET, CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Ofimania(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            HEADPHONES,
            KEYBOARD,
            NOTEBOOK,
            TABLET,
            CELL
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computacion/almacenamiento', SOLID_STATE_DRIVE],
            ['computacion/audifonos', HEADPHONES],
            ['computacion/mouse-y-teclado', KEYBOARD],
            ['computacion/notebooks', NOTEBOOK],
            ['computacion/tablets', TABLET],
            ['telefonia', CELL]
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://ofimania.cl/categoria-producto/' \
                              '{}/page/{}/?per_page=36' \
                              '&_pjax=.main-page-wrapper'.format(
                                url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'products')
                if not product_containers or soup.find('h3', 'title'):
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers.findAll(
                        'div', 'product-grid-item'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, allow_redirects=False)
        if response.status_code == 301:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find('form', 'variations_form'):
            json_container = json.loads(soup.find('form', 'variations_form')[
                                            'data-product_variations'])
            stock = int(BeautifulSoup(json_container[0]['availability_html'],
                                      'html.parser').text.split()[0])
        elif soup.find('p', 'available-on-backorder'):
            stock = 0
        elif soup.find('p', 'stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = -1

        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        price = Decimal(
            remove_words(soup.find('p', 'price').find('span').text))
        picture_urls = [tag['src'].split('?')[0] for tag in
                        soup.find('div',
                                  'woocommerce-product-gallery').findAll(
                            'img')]
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
            picture_urls=picture_urls
        )
        return [p]
