import html
import json
import logging
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import NOTEBOOK, CPU_COOLER, CASE_FAN, \
    STORAGE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, RAM, MONITOR, MOUSE, \
    HEADPHONES, MOTHERBOARD, PROCESSOR, VIDEO_CARD, TABLET, GAMING_CHAIR, \
    ALL_IN_ONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, \
    session_with_proxy


class NiceOne(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            COMPUTER_CASE,
            ALL_IN_ONE,
            MOUSE,
            HEADPHONES,
            MOTHERBOARD,
            MONITOR,
            PROCESSOR,
            VIDEO_CARD,
            RAM,
            POWER_SUPPLY,
            CPU_COOLER,
            NOTEBOOK,
            CASE_FAN,
            TABLET,
            GAMING_CHAIR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_urls = [
            ['22-discos-duros', STORAGE_DRIVE],
            ['24-gabinetes', COMPUTER_CASE],
            ['26-computadores-armados', ALL_IN_ONE],
            ['29-mouse-teclados', MOUSE],
            ['32-parlantes-audio', HEADPHONES],
            ['33-placas-madre', MOTHERBOARD],
            ['34-procesadores', PROCESSOR],
            ['39-tarjetas-graficas', VIDEO_CARD],
            ['27-memorias', RAM],
            ['23-fuentes-de-poder', POWER_SUPPLY],
            ['28-monitores', MONITOR],
            ['61-disipador-por-aire', CPU_COOLER],
            ['62-watercooling', CPU_COOLER],
            ['63-ventiladores', CASE_FAN],
            ['30-notebooks', NOTEBOOK],
            ['68-tablets', TABLET],
            ['73-sillas-gamer', GAMING_CHAIR],
        ]

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) ' \
            'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.149 ' \
            'Safari/537.36'

        product_urls = []
        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                page_url = 'https://n1g.cl/Home/{}?page={}'.format(
                    category_path, page)

                if page > 10:
                    raise Exception('page overflow: ' + page_url)

                soup = BeautifulSoup(session.get(page_url).text, 'html.parser')

                product_cells = soup.findAll('article', 'product-miniature')

                if not product_cells:
                    if page == 1:
                        logging.warning('Empty category: {}'.format(
                            category_path))

                    break

                for cell in product_cells:
                    product_url = cell.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) ' \
            'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.149 ' \
            'Safari/537.36'

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')
        name = soup.find('h1').text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value']

        stock_match = re.search(r"var product_stocks_list = '(.+)';",
                                page_source)
        stock = 0
        if stock_match:
            stock_data = json.loads(html.unescape(stock_match.groups()[0]))[0]

            for stock_entry in stock_data:
                # Some SKUs have negative stocks, no idea why
                stock += max(int(stock_entry.get('available_quantity', 0)), 0)

        price_containers = soup.find('div', 'product-prices')
        offer_price = Decimal(soup.find(
            'span', {'itemprop': 'price'})['content'])
        normal_price = price_containers.find('span', 'regular-price')
        if normal_price:
            normal_price = Decimal(normal_price.text.replace(
                '\xa0$', '').replace('.', ''))
        else:
            normal_price = offer_price

        description = html_to_markdown(str(soup.find('div', 'product_desc')))
        pictures_containers = soup.findAll('img', 'js-thumb')

        if pictures_containers:
            picture_urls = [x['data-image-large-src'] for x in
                            pictures_containers]
        else:
            picture_urls = None

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
