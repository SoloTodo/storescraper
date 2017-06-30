from celery import shared_task, group

from .product import Product
from .utils import get_store_class_by_name, chunks


class Store:
    preferred_queue = 'us'
    preferred_discover_urls_concurrency = 5
    preferred_products_for_url_concurrency = 40
    prefer_async = True

    @classmethod
    def products(cls, product_types=None, async=None, extra_args=None,
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

        if async is None:
            async = cls.prefer_async

        if queue is None:
            queue = cls.preferred_queue

        if discover_urls_concurrency is None:
            discover_urls_concurrency = cls.preferred_discover_urls_concurrency

        if products_for_url_concurrency is None:
            products_for_url_concurrency = \
                cls.preferred_products_for_url_concurrency

        discovered_urls_with_types = []

        if async:
            # 1. URL discovery

            product_types_chunks = chunks(
                product_types, discover_urls_concurrency)

            for product_type_chunk in product_types_chunks:
                chunk_tasks = []

                for product_type in product_type_chunk:
                    task = cls.discover_urls_task.s(
                        cls.__name__, product_type, extra_args)
                    task.set(queue='storescraper_discover_urls_' + queue)
                    chunk_tasks.append(task)
                tasks_group = group(*chunk_tasks)()

                for idx, task_result in enumerate(tasks_group.get()):
                    product_type = product_type_chunk[idx]
                    for discovered_url in task_result:
                        discovered_urls_with_types.append({
                            'url': discovered_url,
                            'product_type': product_type
                        })
        else:
            for product_type in product_types:
                for url in cls.discover_urls(product_type, extra_args):
                    discovered_urls_with_types.append({
                        'url': url,
                        'product_type': product_type
                    })

        return cls.products_for_urls(
            discovered_urls_with_types,
            async=async,
            extra_args=extra_args,
            queue=queue,
            products_for_url_concurrency=products_for_url_concurrency)

    @classmethod
    def products_for_urls(cls, discovery_urls_with_types, async=None,
                          extra_args=None, queue=None,
                          products_for_url_concurrency=None):
        if async is None:
            async = cls.prefer_async

        if queue is None:
            queue = cls.preferred_queue

        if products_for_url_concurrency is None:
            products_for_url_concurrency = \
                cls.preferred_products_for_url_concurrency

        products = []

        if async:
            discovered_urls_with_types_chunks = chunks(
                discovery_urls_with_types, products_for_url_concurrency)

            for discovered_urls_with_types_chunk in \
                    discovered_urls_with_types_chunks:
                chunk_tasks = []

                for discovered_url_entry in discovered_urls_with_types_chunk:
                    task = cls.products_for_url_task.s(
                        cls.__name__, discovered_url_entry['url'],
                        discovered_url_entry['product_type'], extra_args)
                    task.set(queue='storescraper_products_for_url_' + queue)
                    chunk_tasks.append(task)

                tasks_group = group(*chunk_tasks)()

                for task_result in tasks_group.get():
                    for serialized_product in task_result:
                        product = Product(**serialized_product)
                        products.append(product)
        else:
            for discovered_url_entry in discovery_urls_with_types:
                products.extend(cls.products_for_url(
                    discovered_url_entry['url'],
                    discovered_url_entry['product_type'],
                    extra_args))

        return products

    ##########################################################################
    # Celery tasks wrappers
    ##########################################################################

    @staticmethod
    @shared_task
    def products_task(store_class_name, product_types=None, async=True,
                      extra_args=None, queue=None,
                      discover_urls_concurrency=None,
                      products_for_url_concurrency=None):
        store = get_store_class_by_name(store_class_name)
        return store.products(product_types, async, extra_args, queue,
                              discover_urls_concurrency,
                              products_for_url_concurrency)

    @staticmethod
    @shared_task
    def products_for_urls_task(store_class_name, urls_with_product_types=None,
                               async=True, extra_args=None, queue=None):
        store = get_store_class_by_name(store_class_name)
        return store.products_for_urls(urls_with_product_types, async,
                                       extra_args,
                                       queue)

    @staticmethod
    @shared_task
    def products_for_url_task(store_class_name, url, product_type=None,
                              extra_args=None):
        store = get_store_class_by_name(store_class_name)
        raw_products = store.products_for_url(
            url, product_type, extra_args)

        serialized_products = [p.serialize() for p in raw_products]
        return serialized_products

    @staticmethod
    @shared_task
    def discover_urls_task(store_class_name, product_type, extra_args=None):
        store = get_store_class_by_name(store_class_name)
        return store.discover_urls(product_type, extra_args)

    ##########################################################################
    # Implementation dependant methods
    ##########################################################################

    @classmethod
    def product_types(cls):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    @classmethod
    def products_for_url(cls, url, product_type=None, extra_args=None):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    @classmethod
    def discover_urls(cls, product_type, extra_args=None):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')
