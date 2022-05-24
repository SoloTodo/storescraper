import logging

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, KEYBOARD, MEMORY_CARD, \
    MONITOR, PROCESSOR, RAM, SOLID_STATE_DRIVE, WEARABLE, NOTEBOOK
from storescraper.stores.mercado_libre_chile import MercadoLibreChile
from storescraper.utils import session_with_proxy


class EForest(MercadoLibreChile):
    @classmethod
    def categories(cls):
        return [
            MEMORY_CARD,
            KEYBOARD,
            RAM,
            PROCESSOR,
            MONITOR,
            WEARABLE,
            HEADPHONES,
            SOLID_STATE_DRIVE,
            NOTEBOOK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['perifericos-pc-mouses-teclados', KEYBOARD],
            ['componentes-pc-memorias-ram', RAM],
            ['componentes-pc-procesadores', PROCESSOR],
            ['componentes-pc-discos-accesorios', SOLID_STATE_DRIVE],
            ['monitores-accesorios', MONITOR],
            ['relojes-joyas', WEARABLE],
            ['electronica', HEADPHONES],
            ['celulares-telefonia/accesorios-celulares/memorias', MEMORY_CARD],
            ['apple', NOTEBOOK],
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
                url_webpage = 'https://www.eforest.cl/listado/' \
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
        # Remove the seller because we consider MecadoLibreLg to be a
        # standalone retailer, in particular because the LG WTB system
        # only displays entries without a seller (not from marketplaces)
        # and we want to consider MercadoLibreLG for that.
        products = super().products_for_url(
            url, category=category, extra_args=extra_args)

        for product in products:
            product.seller = None

        return products
