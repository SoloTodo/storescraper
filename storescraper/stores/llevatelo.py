import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import TELEVISION, STEREO_SYSTEM, \
    OPTICAL_DISK_PLAYER, CELL, WASHING_MACHINE, REFRIGERATOR, OVEN, \
    AIR_CONDITIONER, VACUUM_CLEANER, HEADPHONES, MONITOR


class Llevatelo(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            STEREO_SYSTEM,
            OPTICAL_DISK_PLAYER,
            CELL,
            WASHING_MACHINE,
            REFRIGERATOR,
            OVEN,
            AIR_CONDITIONER,
            VACUUM_CLEANER,
            HEADPHONES,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('electronica/televisores', TELEVISION),
            ('electronica/telefonia', CELL),
            ('electronica/audio', STEREO_SYSTEM),
            ('electronica/audio/audifonos', HEADPHONES),
            ('climatizacion/equipos-de-climatizacion/', AIR_CONDITIONER),
            ('electrodomesticos/hornos-electricos-y-microondas/', OVEN),
            ('limpieza/aspiradoras/', VACUUM_CLEANER),
            ('empotrados/', OVEN),
            ('linea-blanca/lavadoras', WASHING_MACHINE),
            ('linea-blanca/secadoras-de-ropa', WASHING_MACHINE),
            ('linea-blanca/refrigeradores', REFRIGERATOR),
            ('computacion/monitores', MONITOR),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.llevatelo.cl/categoria-producto/{}/page/' \
                      '{}/'.format(category_path, page)

                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                items = soup.findAll('li', 'product')

                if not items:
                    if page == 1:
                        logging.warning('No products for {}'.format(url))
                    break

                for item in items:
                    product_url = item.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        sku = soup.find('span', 'sku').text.strip()
        name = soup.find('h1', 'product_title').text.strip() + \
            " ({})".format(sku)

        if soup.find('p', 'out-of-stock'):
            stock = 0
        else:
            stock = -1

        price_container = soup.find('div', 'summary').findAll(
            'span', 'amount')[-1]
        price = Decimal(price_container.text.replace('$', '').replace('.', ''))

        pictures_containers = soup.findAll(
            'div', 'woocommerce-product-gallery__image')
        picture_urls = []

        for picture_container in pictures_containers:
            picture_url = picture_container.find('a')['href']
            picture_urls.append(picture_url)

        description = html_to_markdown(str(soup.find(
            'div', 'woocommerce-product-details__short-description')))

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
            description=description,
            picture_urls=picture_urls)

        return [p]
