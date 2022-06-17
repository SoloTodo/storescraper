import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, PRINTER, MONITOR, \
    STORAGE_DRIVE, HEADPHONES, KEYBOARD, WEARABLE, ALL_IN_ONE, TABLET
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class NotebooksYa(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            PRINTER,
            MONITOR,
            STORAGE_DRIVE,
            HEADPHONES,
            KEYBOARD,
            WEARABLE,
            ALL_IN_ONE,
            TABLET,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['portatiles', NOTEBOOK],
            ['computadores', ALL_IN_ONE],
            ['impresion', PRINTER],
            ['pantallas-y-tvs', MONITOR],
            ['almacenamiento', STORAGE_DRIVE],
            ['partes-y-piezas', STORAGE_DRIVE],
            ['audifonos', HEADPHONES],
            ['audio-y-video', HEADPHONES],
            ['teclados-mouse', KEYBOARD],
            ['relojes', WEARABLE],
            ['product-category/macbook', NOTEBOOK],
            ['product-category/imac-ya', ALL_IN_ONE],
            ['product-category/ipads-ya', TABLET],
            ['product-category/apple-watch', WEARABLE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            local_product_urls = []
            done = False
            while not done:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://notebooksya.cl/{}/page/{}'.format(
                    url_extension, page)
                print(url_webpage)

                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in local_product_urls:
                        done = True
                        break
                    local_product_urls.append(product_url)
                page += 1
            product_urls.extend(local_product_urls)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find('h1', 'product_title'):
            name = soup.find('h1', 'product_title').text
        else:
            name = soup.find('div', 'et_pb_module et_pb_wc_title '
                                    'et_pb_wc_title_0 '
                                    'et_pb_bg_layout_light').text.strip()
        key = soup.find('link', {'rel': 'shortlink'})[
            'href'].split('=')[-1]
        stock = 0
        qty_input = soup.find('input', 'input-text qty text')
        if qty_input:
            if qty_input['max']:
                stock = int(qty_input['max'])
            else:
                stock = -1
        price_container = soup.find('div', 'wds')
        offer_container = price_container.find('div', 'wds-first')
        offer_price = Decimal(remove_words(
            offer_container.findAll('bdi')[-1].text))
        normal_container = price_container.find('div', 'wds-second')
        normal_price = Decimal(remove_words(
            normal_container.findAll('bdi')[-1].text))
        picture_urls = [tag['src'] for tag in soup.find('div',
                        'woocommerce-product-gallery').findAll('img')]
        description = soup.find(
            'meta', {'property': 'og:description'})['content']

        sku_tag = soup.find('span', 'sku')
        if sku_tag:
            sku = sku_tag.text.strip()
        else:
            sku = None

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
