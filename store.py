import importlib
from celery import shared_task

from utils import get_store_class_by_name


class Store:
    preferred_queue = 'us'
    discover_urls_concurrency = 3
    products_for_url_concurrency = 10

    @classmethod
    def products(cls, product_types=None, async=True, extra_args=None,
                 queue=None, discover_urls_concurrency=None,
                 products_for_url_concurrency=None):

        # If product_types is None, initialize it with the ones that the store
        # can handle. Otherwise filter out the types that the store can't
        # handle
        if product_types is None:
            product_types = cls.product_types()
        else:
            product_types = [ptype for ptype in cls.product_types()
                             if ptype in product_types]

    ##########################################################################
    # Celery tasks wrapping
    ##########################################################################

    @staticmethod
    @shared_task
    def products_task(store_path, product_types=None, async=True,
                      extra_args=None, queue=None,
                      discover_urls_concurrency=None,
                      products_for_url_concurrency=None):
        store = get_store_class_by_name(store_path)
        return store.products(product_types, async, extra_args, queue,
                              discover_urls_concurrency,
                              products_for_url_concurrency)

    @staticmethod
    @shared_task
    def products_for_urls_task(store_path, urls_with_product_types=None,
                               async=True, extra_args=None, queue=None):
        store = get_store_class_by_name(store_path)
        return store.products_for_urls(urls_with_product_types, async,
                                       extra_args,
                                       queue)

    @staticmethod
    @shared_task
    def products_for_url_task(store_path, url, product_type=None,
                              extra_args=None, discovery_information=None):
        store = get_store_class_by_name(store_path)
        raw_products = store.products_for_url(
            url, product_type, extra_args, discovery_information)

        serialized_products = [p.serialize() for p in raw_products]
        return serialized_products

    @staticmethod
    @shared_task
    def discover_urls_task(store_path, product_type, extra_args=None):
        store = get_store_class_by_name(store_path)
        return store.discover_urls(product_type, extra_args)

    ##########################################################################
    # Implementation dependant methods
    ##########################################################################

    @classmethod
    def product_types(cls):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    @classmethod
    def products_for_url(cls, url, product_type=None, extra_args=None,
                         discovery_information=None):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    @classmethod
    def discover_urls(cls, product_type, extra_args=None):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')
