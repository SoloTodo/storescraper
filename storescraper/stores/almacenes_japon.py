import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import STEREO_SYSTEM, AIR_CONDITIONER, OVEN, \
    WASHING_MACHINE, CELL, TELEVISION, REFRIGERATOR, CELL_ACCESORY
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class AlmacenesJapon(Store):
    @classmethod
    def categories(cls):
        return [
            STEREO_SYSTEM,
            AIR_CONDITIONER,
            OVEN,
            WASHING_MACHINE,
            CELL,
            TELEVISION,
            REFRIGERATOR,
            CELL_ACCESORY,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['3-audio', STEREO_SYSTEM],
            ['10-climatizacion', AIR_CONDITIONER],
            ['13-cocina', OVEN],
            ['30-lavado-y-secado', WASHING_MACHINE],
            ['51-celulares', CELL],
            ['55-tv-y-video', TELEVISION],
            ['62-refrigeración', REFRIGERATOR],
            ['79-cuidado-personal', CELL_ACCESORY],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for url_extension, local_category in url_extensions:
            if category != local_category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = r'https://www.almacenesjapon.com/{}?q=Marca-LG' \
                              '&page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('article',
                                                  'product-miniature')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break

                for product in product_containers:
                    product_url = product.find('a')['href']
                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        if response.status_code == 403:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product-detail-name').text.strip()
        sku = soup.find('span', 'item-code').text.strip()
        stock = 0
        if soup.find('link', {'itemprop': 'availability'})['href'] \
                == 'https://schema.org/InStock':
            stock = -1
        price = Decimal(soup.find('h4', {'itemprop': 'price'}).
                        text.replace('$', '').replace('.', '').
                        replace(',', '.').strip())

        picture_urls = [soup.find('meta', {'property': 'og:image'})['content']]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'full_spec'})))

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
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
