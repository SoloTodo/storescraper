import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import TELEVISION, STEREO_SYSTEM, CELL, \
    REFRIGERATOR, OVEN, AIR_CONDITIONER, WASHING_MACHINE, STOVE, MONITOR, \
    HEADPHONES


class Jetstereo(Store):
    base_url = 'https://www.jetstereo.com'

    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            STEREO_SYSTEM,
            CELL,
            REFRIGERATOR,
            OVEN,
            AIR_CONDITIONER,
            WASHING_MACHINE,
            STOVE,
            MONITOR,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('tvs', TELEVISION),
            ('audio-portatil', STEREO_SYSTEM),
            ('equipos-de-sonido', STEREO_SYSTEM),
            ('teatros-en-casa', STEREO_SYSTEM),
            ('smartphones', CELL),
            ('refrigeradoras-side-by-side', REFRIGERATOR),
            ('refrigeradoras-french-door', REFRIGERATOR),
            ('refrigeradoras-twin', REFRIGERATOR),
            ('refrigeradora-top-mount', REFRIGERATOR),
            ('microondas', OVEN),
            ('hornos', OVEN),
            ('aire-acondicionado', AIR_CONDITIONER),
            ('twinwash', WASHING_MACHINE),
            ('lavadoras-top-load', WASHING_MACHINE),
            ('lavadora-carga-frontal', WASHING_MACHINE),
            ('secadoras', WASHING_MACHINE),
            ('estufas-electricas', STOVE),
            ('estufas-de-gas', STOVE),
            ('monitores', MONITOR),
            ('audifonos', HEADPHONES),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            local_urls = []
            done = False

            while not done:
                url = '{}/{}?pv=50&page={}'.format(
                    cls.base_url, category_path, page)
                print(url)

                if page > 20:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url, verify=False).text,
                                     'html.parser')
                containers = soup.findAll('div', 'product-slide-entry')

                if not containers:
                    logging.warning('Empty category: ' + url)
                    break

                for container in containers:
                    product_title = container.find('a', 'title')
                    product_url = '{}{}'\
                        .format(cls.base_url, container.find('a')['href'])
                    if (product_title, product_url) in local_urls:
                        done = True
                        break
                    local_urls.append((product_title, product_url))

                page += 1

            for product_title, product_url in local_urls:
                if 'LG' in product_title.text.upper():
                    product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url, allow_redirects=False, verify=False)

        if data.status_code == 302:
            return []

        soup = BeautifulSoup(data.text, 'html.parser')
        sku_container = soup.find('div', 'star')

        if not sku_container:
            return []

        sku = sku_container.find('h4').text.replace('SKU: ', '').strip()
        name = '{} ({})'\
            .format(soup.find('div', 'article-container').find('h1').text, sku)

        if soup.find('div', 'share-box').find('a', 'add-to-cart-btn'):
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('div', 'price').find('div', 'current')
                        .text.strip().replace('L. ', '').replace(',', ''))

        picture_urls = []
        pictures = soup.findAll('div', 'product-zoom-image')

        for picture in pictures:
            picture_url = picture.find('img')['src'].replace(' ', '%20')
            if 'https:' not in picture_url:
                picture_url = '{}{}'.format(cls.base_url, picture_url)
            picture_urls.append(picture_url)

        description = html_to_markdown(str(soup.find('ul', 'read-more-wrap')))

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
            'HNL',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
