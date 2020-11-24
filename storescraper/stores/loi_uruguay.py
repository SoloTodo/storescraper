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
            'https://90i0mrelm2-dsn.algolia.net/1/indexes/*/queries?x-'
            'algolia-application-id=90I0MRELM2&x-algolia-api-key=f1b9f85e'
            'ae8df13ab13361ccfe4793d7',
            '{"requests":[{"indexName":"uy_products_date_desc","params":'
            '"query=lg"}]}')

        product_urls = []

        for entry in res.json()['results'][0]['hits']:
            product_urls.append(entry['product_url'])

        return product_urls
