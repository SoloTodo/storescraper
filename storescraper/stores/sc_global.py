import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy
from storescraper.categories import NOTEBOOK, PRINTER, ALL_IN_ONE, MOUSE, \
    MONITOR, HEADPHONES, UPS, GAMING_CHAIR, TABLET, RAM, \
    SOLID_STATE_DRIVE, PROCESSOR, VIDEO_CARD


class ScGlobal(StoreWithUrlExtensions):
    url_extensions = [
        ['workstations-31', NOTEBOOK],
        ['alto-rendimiento-32', NOTEBOOK],
        ['hogar-y-empresa-33', NOTEBOOK],
        ['equipos-empresariales-23', NOTEBOOK],
        ['notebook-gamer-89', NOTEBOOK],
        ['notebook-10', NOTEBOOK],
        ['plotter-hp-100', PRINTER],
        ['ups-69', UPS],
        ['ups-85', UPS],
        ['all-in-one-22', ALL_IN_ONE],
        ['monitores-17', MONITOR],
        ['monitor-gamer-90', MONITOR],
        ['impresion-12', PRINTER],
        ['tablet-11', TABLET],
        ['memoria-ram-29', RAM],
        ['discos-duros-30', SOLID_STATE_DRIVE],
        ['teclados-mouse-76', MOUSE],
        ['audifonos-78', HEADPHONES],
        ['silla-gamer-74', GAMING_CHAIR],
        ['silla-gamer-88', GAMING_CHAIR],
        ['procesadores-94', PROCESSOR],
        ['tarjetas-de-video-56', VIDEO_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)

        product_urls = []
        page = 1

        while True:
            category_url = 'https://www.scglobal.cl/{}?' \
                           'page={}'.format(url_extension, page)
            print(category_url)

            if page >= 10:
                raise Exception('Page overflow: ' + category_url)

            response = session.get(category_url, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')

            if not soup.find('div', 'products row'):
                if page == 1:
                    logging.warning('Empty category: ' + category_url)
                break

            product_cells = soup.findAll('article', 'product-miniature')

            for cell in product_cells:
                product_url = cell.find('a')['href']
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url, verify=False).text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value']

        pricing_container = soup.find('span', {'itemprop': 'price'})
        price = Decimal(pricing_container['content'])
        part_number_tag = soup.find('span', {'itemprop': 'sku'})
        if not part_number_tag:
            return []
        part_number = part_number_tag.text.strip()
        add_to_cart_button = soup.find('button', 'add-to-cart')

        if add_to_cart_button.get('disabled') is None:
            stock = -1
        else:
            stock = 0

        picture_urls = [tag.find('img')['data-image-large-src'] for tag in
                        soup.find('ul', 'product-images')
                            .findAll('li', 'thumb-container')]

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
            part_number=part_number,
            picture_urls=picture_urls
        )

        return [p]
