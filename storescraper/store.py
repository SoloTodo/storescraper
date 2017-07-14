import traceback

from celery import shared_task, group
from celery.utils.log import get_task_logger

from .product import Product
from .utils import get_store_class_by_name, chunks

logger = get_task_logger(__name__)


class StoreScrapError(Exception):
    def __init__(self, message):
        super(StoreScrapError, self).__init__(message)


class Store:
    preferred_queue = 'us'
    preferred_discover_urls_concurrency = 3
    preferred_products_for_url_concurrency = 10

    ##########################################################################
    # API methods
    ##########################################################################

    @classmethod
    def products(cls, product_types=None, extra_args=None,
                 queue=None, discover_urls_concurrency=None,
                 products_for_url_concurrency=None, async=True):
        if product_types is None:
            product_types = cls.product_types()
        else:
            product_types = [ptype for ptype in cls.product_types()
                             if ptype in product_types]

        if queue is None:
            queue = cls.preferred_queue

        if discover_urls_concurrency is None:
            discover_urls_concurrency = cls.preferred_discover_urls_concurrency

        if products_for_url_concurrency is None:
            products_for_url_concurrency = \
                cls.preferred_products_for_url_concurrency

        logger.info('Obtaining products from: {}'.format(cls.__name__))

        discovered_urls_with_types = cls.discover_urls_for_product_types(
            product_types=product_types,
            extra_args=extra_args,
            queue=queue,
            discover_urls_concurrency=discover_urls_concurrency,
            async=async
        )

        return cls.products_for_urls(
            discovered_urls_with_types,
            extra_args=extra_args,
            queue=queue,
            products_for_url_concurrency=products_for_url_concurrency,
            async=async
        )

    @classmethod
    def discover_urls_for_product_types(cls, product_types=None,
                                        extra_args=None, queue=None,
                                        discover_urls_concurrency=None,
                                        async=True):
        if product_types is None:
            product_types = cls.product_types()
        else:
            product_types = [ptype for ptype in cls.product_types()
                             if ptype in product_types]

        if queue is None:
            queue = cls.preferred_queue

        if discover_urls_concurrency is None:
            discover_urls_concurrency = cls.preferred_discover_urls_concurrency

        logger.info('Discovering URLs for: {}'.format(cls.__name__))

        discovered_urls_with_types = []

        if async:
            product_type_chunks = chunks(
                product_types, discover_urls_concurrency)

            for product_type_chunk in product_type_chunks:
                chunk_tasks = []

                logger.info('Discovering URLs for: {}'.format(
                    product_type_chunk))

                for product_type in product_type_chunk:
                    task = cls.discover_urls_for_product_type_task.s(
                        cls.__name__, product_type, extra_args)
                    task.set(queue='storescraper_discover_urls_for_'
                                   'product_type_' + queue)
                    chunk_tasks.append(task)
                tasks_group = cls.create_celery_group(chunk_tasks)

                for idx, task_result in enumerate(tasks_group.get()):
                    product_type = product_type_chunk[idx]
                    logger.info('Discovered URLs for {}:'.format(product_type))
                    for discovered_url in task_result:
                        logger.info(discovered_url)
                        discovered_urls_with_types.append({
                            'url': discovered_url,
                            'product_type': product_type
                        })
        else:
            logger.info('Using sync method')
            for product_type in product_types:
                for url in cls.discover_urls_for_product_type(
                        product_type, extra_args):
                    logger.info('Discovered URL: {} ({})'.format(
                        url, product_type))
                    discovered_urls_with_types.append({
                        'url': url,
                        'product_type': product_type
                    })

        return discovered_urls_with_types

    @classmethod
    def products_for_urls(cls, discovery_urls_with_types, extra_args=None,
                          queue=None, products_for_url_concurrency=None,
                          async=True):
        if queue is None:
            queue = cls.preferred_queue

        if products_for_url_concurrency is None:
            products_for_url_concurrency = \
                cls.preferred_products_for_url_concurrency

        logger.info('Retrieving products for: {}'.format(cls.__name__))

        for entry in discovery_urls_with_types:
            logger.info('{} ({})'.format(entry['url'], entry['product_type']))

        products = []
        discovery_urls_without_products = []

        if async:
            discovery_urls_with_types_chunks = chunks(
                discovery_urls_with_types, products_for_url_concurrency)

            for discovery_urls_with_types_chunk in \
                    discovery_urls_with_types_chunks:
                chunk_tasks = []

                for discovered_url_entry in discovery_urls_with_types_chunk:
                    logger.info('Retrieving URL: {}'.format(discovered_url_entry['url']))
                    task = cls.products_for_url_task.s(
                        cls.__name__, discovered_url_entry['url'],
                        discovered_url_entry['product_type'], extra_args)
                    task.set(queue='storescraper_products_for_url_' + queue)
                    chunk_tasks.append(task)

                tasks_group = cls.create_celery_group(chunk_tasks)

                for idx, task_result in enumerate(tasks_group.get()):
                    for serialized_product in task_result:
                        product = Product.deserialize(serialized_product)
                        logger.info('{}\n'.format(product))
                        products.append(product)

                    if not task_result:
                        discovery_urls_without_products.append(
                            discovery_urls_with_types_chunk[idx]['url'])
        else:
            logger.info('Using sync method')
            for discovered_url_entry in discovery_urls_with_types:
                retrieved_products = cls.products_for_url(
                    discovered_url_entry['url'],
                    discovered_url_entry['product_type'],
                    extra_args)

                for product in retrieved_products:
                    logger.info('{}\n'.format(product))
                    products.append(product)

                if not retrieved_products:
                    discovery_urls_without_products.append(
                        discovered_url_entry['url'])

        return {
            'products': products,
            'discovery_urls_without_products': discovery_urls_without_products
        }

    ##########################################################################
    # Celery tasks wrappers
    ##########################################################################

    @staticmethod
    @shared_task
    def discover_urls_for_product_type_task(store_class_name, product_type,
                                            extra_args=None):
        store = get_store_class_by_name(store_class_name)
        logger.info('Discovering URLs')
        logger.info('Store: ' + store.__name__)
        logger.info('Product type: ' + product_type)
        try:
            discovered_urls = store.discover_urls_for_product_type(
                product_type, extra_args)
        except Exception:
            error_message = 'Error discovering URLs from {}: {} - {}'.format(
                store_class_name,
                product_type,
                traceback.format_exc())
            logger.error(error_message)
            raise StoreScrapError(error_message)

        for idx, url in enumerate(discovered_urls):
            logger.info('{} - {}'.format(idx, url))
        return discovered_urls

    @staticmethod
    @shared_task
    def products_for_url_task(store_class_name, url, product_type=None,
                              extra_args=None):
        store = get_store_class_by_name(store_class_name)
        logger.info('Obtaining products for URL')
        logger.info('Store: ' + store.__name__)
        logger.info('Product type: ' + product_type)
        logger.info('URL: ' + url)

        try:
            raw_products = store.products_for_url(
                url, product_type, extra_args)
        except Exception:
            error_message = 'Error retrieving products from {}: {} - {}'.format(
                store_class_name,
                url,
                traceback.format_exc())
            logger.error(error_message)
            raise StoreScrapError(error_message)

        serialized_products = [p.serialize() for p in raw_products]

        for idx, product in enumerate(serialized_products):
            logger.info('{} - {}'.format(idx, product))

        return serialized_products

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
    def discover_urls_for_product_type(cls, product_type, extra_args=None):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    ##########################################################################
    # Utility methods
    ##########################################################################

    @classmethod
    def create_celery_group(cls, tasks):
        # REF: https://stackoverflow.com/questions/41371933/why-is-this-
        # construction-of-a-group-of-chains-causing-an-exception-in-celery
        if len(tasks) == 1:
            g = group(tasks)()
        else:
            g = group(*tasks)()
        return g
