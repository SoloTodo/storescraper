from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import HEADPHONES, NOTEBOOK, TABLET, TELEVISION, \
    WEARABLE, USB_FLASH_DRIVE, UPS, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class TicOnlineStore(Store):
    @classmethod
    def categories(cls):
        return [
            USB_FLASH_DRIVE,
            NOTEBOOK,
            TELEVISION,
            TABLET,
            HEADPHONES,
            WEARABLE,
            UPS,
            ALL_IN_ONE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accesorios/categoria-removibles', USB_FLASH_DRIVE],
            ['audiovisual/categoria-audifonos', HEADPHONES],
            ['audiovisual/audio-y-video', HEADPHONES],
            ['computacion/categoria-computadores-de-mesa', UPS],
            ['computacion/portatiles', NOTEBOOK],
            ['computacion/tabletas', TABLET],
            ['computacion/categoria-todo-en-uno', ALL_IN_ONE],
            ['electro/televisores', TELEVISION],
            ['wearables', WEARABLE],
            ['zona-gamer', HEADPHONES],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://tic-online-store.cl/categoria-prod' \
                              'ucto/{}/page/{}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'li', 'product')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
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

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)
        for entry in json_data['@graph']:
            if entry['@type'] == 'Product':
                product_data = entry
                break
        else:
            raise Exception('No JSON product data found')

        name = product_data['name']
        description = product_data['description']

        products = []
        if soup.find('form', 'variations_form'):
            variations = json.loads(soup.find('form', 'variations_form')[
                                        'data-product_variations'])
            for product in variations:
                variation_name = name + ' - ' + product['attributes'][
                    'attribute_pa_color']
                sku = str(product['variation_id'])
                if product['max_qty'] == '':
                    stock = 0
                else:
                    stock = product['max_qty']
                price = Decimal(product['display_price'])
                picture_urls = [product['image']['url']]
                p = Product(
                    variation_name,
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
                    picture_urls=picture_urls,
                    description=description
                )
                products.append(p)
        else:
            key = soup.find(
                'link', {'rel': 'shortlink'})['href'].split('?p=')[-1]
            sku = str(product_data['sku'])

            price = Decimal(remove_words(
                soup.find('p', 'price').findAll('bdi')[-1].text))

            cart_btn = soup.find('button', {'name': 'add-to-cart'})
            if cart_btn:
                input_qty = soup.find('input', 'input-text qty text')
                if input_qty:
                    if 'max' in input_qty.attrs and input_qty['max']:
                        stock = int(input_qty['max'])
                    else:
                        stock = -1
                else:
                    stock = 1
            else:
                stock = 0

            picture_urls = []
            container = soup.find('figure',
                                  'woocommerce-product-gallery__wrapper')
            for a in container.findAll('a'):
                picture_urls.append(a['href'])

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
                picture_urls=picture_urls,
                description=description
            )
            products.append(p)
        return products
