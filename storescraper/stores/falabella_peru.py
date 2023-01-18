from storescraper.categories import TELEVISION
from storescraper.store import Store
from storescraper.utils import session_with_proxy, \
    CF_REQUEST_HEADERS


class FalabellaPeru(Store):
    store_and_subdomain = None
    seller = 'FALABELLA'

    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # ONLY CONSIDERS LG SKUs

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = CF_REQUEST_HEADERS['User-Agent']

        discovered_urls = []
        page = 1

        while True:
            if page >= 50:
                raise Exception('Page overflow')

            endpoint = 'https://www.falabella.com.pe/s/browse/v1/brand/pe' \
                       '?page={}&brandName=LG&zones=912_LIMA_2%2CLIMA_URB1_' \
                       'DIRECTO%2CURBANO_83%2COLVAA_36%2C912_LIMA_1%2C' \
                       '150101%2CIBIS_21%2CPERF_TEST%2C150000'.format(page)

            if cls.store_and_subdomain:
                endpoint += '&subdomain={}&store={}'.format(
                    cls.store_and_subdomain, cls.store_and_subdomain)

            if cls.seller:
                endpoint += '&f.derived.variant.sellerId={}'.format(
                    cls.seller)

            res = session.get(endpoint).json()

            if not res['data']['results']:
                break

            for product_entry in res['data']['results']:
                discovered_urls.append(product_entry['url'])

            page += 1

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        from .falabella import Falabella

        products = Falabella.products_for_url(
            url, category=category, extra_args=extra_args)

        for product in products:
            product.store = cls.__name__
            product.currency = 'PEN'
            product.url = url
            product.discovery_url = url

        return products
