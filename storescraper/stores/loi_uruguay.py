from .loi_chile import LoiChile
from ..categories import TELEVISION
from ..utils import session_with_proxy


class LoiUruguay(LoiChile):
    CURRENCY = 'USD'
    IMAGE_DOMAIN = 'd391ci4kxgasl8'

    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        res = session.post(
            'https://90i0mrelm2-dsn.algolia.net/1/indexes/*/queries?x-algolia-'
            'agent=Algolia%20for%20JavaScript%20(4.13.0)%3B%20Browser%20(lite)'
            '%3B%20react%20(17.0.2)%3B%20react-instantsearch%20(6.22.0)%3B%20J'
            'S%20Helper%20(3.7.3)&x-algolia-api-key=004b911528dce8b9f9543d1461'
            'c60347&x-algolia-application-id=90I0MRELM2',
            '{"requests":[{"indexName":"uy_products_price_asc","params":"filte'
            'rs=product_enabled%3A1&query=lg"}]}')

        product_urls = []

        for entry in res.json()['results'][0]['hits']:
            product_urls.append(entry['product_url'])

        return product_urls
