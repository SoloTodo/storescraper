import json
import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import MONITOR, HEADPHONES, STEREO_SYSTEM, \
    VIDEO_GAME_CONSOLE, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, \
    parse_categories_from_url_extensions, remove_words


class Nintecno(Store):
    url_extensions = [
        ['audifonos', HEADPHONES],
        ['parlantes-inalambricos', STEREO_SYSTEM],
        ['consolas', VIDEO_GAME_CONSOLE],
        ['notebooks', NOTEBOOK],
        ['monitores', MONITOR],
        ['parlantes-inteligentes', STEREO_SYSTEM],
    ]

    @classmethod
    def categories(cls):
        return parse_categories_from_url_extensions(cls.url_extensions)

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in cls.url_extensions:
            if local_category != category:
                continue

            page = 1
            local_urls = []
            done = False

            while not done:
                if page >= 50:
                    raise Exception('Page overflow: ' + category_path)

                url_webpage = 'https://nintecno.cl/index.php/' \
                              'product-category/{}/?page={}'.format(
                                category_path, page)

                print(url_webpage)
                response = session.get(url_webpage)

                soup = BeautifulSoup(response.text, 'html.parser')
                link_containers = soup.findAll('div', 'product')

                if not link_containers:
                    logging.warning('Empty category: ' + url_webpage)
                    break

                for link_container in link_containers:
                    product_url = link_container.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break
                    local_urls.append(product_url)

                page += 1

            product_urls.extend(local_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        json_tag = soup.find('script', {'type': 'application/ld+json'})
        json_data = json.loads(json_tag.text)['@graph'][1]
        name = json_data['name'].strip()
        key = str(json_data['sku'])
        description = json_data['description']

        if json_data['offers'][0]['availability'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        prices_table_tag_cells = \
            soup.find('table', 'precios-adicionales').findAll('td')
        assert len(prices_table_tag_cells) == 4

        normal_price = Decimal(remove_words(prices_table_tag_cells[3].text))
        offer_price = Decimal(remove_words(prices_table_tag_cells[1].text))

        picture_urls = [x.find('a')['href'] for x in soup.findAll(
            'div', 'woocommerce-product-gallery__image')]

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
            sku=key,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
