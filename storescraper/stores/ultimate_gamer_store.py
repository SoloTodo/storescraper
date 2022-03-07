import logging
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words
from storescraper.categories import VIDEO_CARD, PROCESSOR, MONITOR, RAM, \
    SOLID_STATE_DRIVE, MOTHERBOARD, HEADPHONES, STORAGE_DRIVE, POWER_SUPPLY, \
    CPU_COOLER, COMPUTER_CASE, GAMING_CHAIR, NOTEBOOK


class UltimateGamerStore(Store):
    @classmethod
    def categories(cls):
        return [
            VIDEO_CARD,
            PROCESSOR,
            MONITOR,
            RAM,
            SOLID_STATE_DRIVE,
            MOTHERBOARD,
            HEADPHONES,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            CPU_COOLER,
            COMPUTER_CASE,
            GAMING_CHAIR,
            NOTEBOOK,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['tarjeta-de-video', VIDEO_CARD],
            ['procesadores', PROCESSOR],
            ['productos/memorias', RAM],
            ['productos/ssd', SOLID_STATE_DRIVE],
            ['productos/accesorios', MONITOR],
            ['placas-madre', MOTHERBOARD],
            ['p-e-r-i-f-e-r-i-c-o-s', HEADPHONES],
            ['d-i-s-c-o-d-u-r-o-1', STORAGE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['productos/refrigeracion', CPU_COOLER],
            ['productos/gabinetes', COMPUTER_CASE],
            ['productos/sillas', GAMING_CHAIR],
            ['productos/notebook', NOTEBOOK],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.ugstore.cl/{}?page={}'.format(
                    category_path, page)
                print(url)

                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                items = soup.findAll('article', 'product-block')

                if not items:
                    if page == 1:
                        logging.warning('Emtpy Path: {}'.format(url))
                    break

                for item in items:
                    product_url = 'https://www.ugstore.cl{}'.format(
                        item.find('a', 'product-block__anchor')['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'product-info__name').text
        key = re.search(r'data.content_ids = \[(\d+)];',
                        page_source).groups()[0]

        if 'PREVENTA' in name.upper():
            stock = 0
        elif soup.find('meta', {'property': 'product:availability'})[
                'content'] == 'instock':
            stock = -1
        else:
            stock = 0

        price = Decimal(remove_words(
            soup.find('span', 'product-info__price-current').text).strip())

        description = html_to_markdown(
            str(soup.find('section', {'id': 'product-description'})))

        picture_urls = [
            i['src'] for i in soup.findAll(
                'img', 'product-slider__block-image')]

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
            sku=key,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
