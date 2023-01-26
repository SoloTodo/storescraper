from .ripley import Ripley
from ..categories import TELEVISION


class RipleyPeru(Ripley):
    # Only returns LG products

    domain = 'https://simple.ripley.com.pe'
    currency = 'PEN'

    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        extra_args = extra_args or {}
        extra_args['brand_filter'] = 'LG'
        raw_product_urls = cls.discover_urls_for_keyword('lg lg', 1000,
                                                         extra_args=extra_args)
        product_urls = []

        for product_url in raw_product_urls:
            if '-pmp' in product_url:
                # Skip marketplace products
                continue
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        extra_args = extra_args or {}
        extra_args['source'] = 'keyword_search'
        return super(RipleyPeru, cls).products_for_url(url, category,
                                                       extra_args=extra_args)
