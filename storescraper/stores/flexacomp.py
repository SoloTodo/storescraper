import logging
from bs4 import BeautifulSoup
from storescraper.categories import CASE_FAN, CELL, COMPUTER_CASE, \
    GAMING_CHAIR, HEADPHONES, MOUSE, NOTEBOOK, POWER_SUPPLY, SOLID_STATE_DRIVE
from storescraper.stores.mercado_libre_chile import MercadoLibreChile
from storescraper.utils import session_with_proxy


class Flexacomp(MercadoLibreChile):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            GAMING_CHAIR,
            CELL,
            HEADPHONES,
            CASE_FAN,
            POWER_SUPPLY,
            SOLID_STATE_DRIVE,
            COMPUTER_CASE,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computacion/notebooks', NOTEBOOK],
            ['celulares-telefonia', CELL],
            ['accesorios-pc-gamin', HEADPHONES],
            ['hogar', GAMING_CHAIR],
            ['componentes-pc-coolers', CASE_FAN],
            ['componentes-pc-fuentes-alimentacion', POWER_SUPPLY],
            ['componentes-pc-discos-accesorios', SOLID_STATE_DRIVE],
            ['componentes-pc-gabinetes-soportes', COMPUTER_CASE],
            ['computacion/perifericos-accesorios/mouses', MOUSE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                index = str(50*(page - 1) + 1)
                url_webpage = 'https://www.flexacomp.cl/listado/' \
                    '{}/_Desde_{}_NoIndex_True'.format(url_extension, index)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'li', 'ui-search-layout__item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a', 'ui-search-link')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super().products_for_url(
            url, category=category, extra_args=extra_args)

        for product in products:
            product.seller = None

        return products
