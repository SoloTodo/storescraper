from bs4 import BeautifulSoup

from storescraper.categories import AIR_CONDITIONER, SPACE_HEATER
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Enel(Store):
    @classmethod
    def categories(cls):
        return [
            AIR_CONDITIONER,
            SPACE_HEATER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['electrodomesticos/climatizacion/aires-acondicionados', AIR_CONDITIONER],
            ['climatizacion-estufas-calefactores-electricos', SPACE_HEATER],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            offset = 1
            done = False

            while not done:
                if offset >= 200:
                    raise Exception('Page overflow')

                category_url = 'https://enelxchile.mercadoshops.cl/listado/' \
                               '{}/_Desde_{}'.format(category_path, offset)
                print(category_url)
                soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
                product_containers = soup.findAll('li', 'ui-search-layout__item')

                if not product_containers:
                    break

                for container in product_containers:
                    product_url = container.find('a')['href'].split('#')[0].split('?')[0]
                    product_urls.append(product_url)

                offset += 50

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        from . import MercadoLibreChile
        products = MercadoLibreChile.products_for_url(url, category,
                                                      extra_args)
        for product in products:
            product.seller = None
            product.store = cls.__name__

        return products
