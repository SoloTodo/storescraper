import traceback

from celery import shared_task, group
from celery.result import allow_join_result
from celery.utils.log import get_task_logger


from .product import Product
from .utils import get_store_class_by_name, chunks

logger = get_task_logger(__name__)


class StoreScrapError(Exception):
    def __init__(self, message):
        super(StoreScrapError, self).__init__(message)


class Store:
    preferred_discover_urls_concurrency = 3
    preferred_products_for_url_concurrency = 10
    prefer_async = True

    ##########################################################################
    # API methods
    ##########################################################################

    @classmethod
    def products(cls, categories=None, extra_args=None,
                 discover_urls_concurrency=None,
                 products_for_url_concurrency=None, use_async=None):
        sanitized_parameters = cls.sanitize_parameters(
            categories=categories,
            discover_urls_concurrency=discover_urls_concurrency,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async)

        categories = sanitized_parameters['categories']
        discover_urls_concurrency = \
            sanitized_parameters['discover_urls_concurrency']
        products_for_url_concurrency = \
            sanitized_parameters['products_for_url_concurrency']
        use_async = sanitized_parameters['use_async']

        logger.info('Obtaining products from: {}'.format(cls.__name__))
        logger.info('Categories: {}'.format(', '.join(categories)))

        discovered_urls_with_categories = cls.discover_urls_for_categories(
            categories=categories,
            extra_args=extra_args,
            discover_urls_concurrency=discover_urls_concurrency,
            use_async=use_async
        )

        return cls.products_for_urls(
            discovered_urls_with_categories,
            extra_args=extra_args,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async
        )

    @classmethod
    def discover_urls_for_categories(cls, categories=None,
                                     extra_args=None,
                                     discover_urls_concurrency=None,
                                     use_async=True):
        sanitized_parameters = cls.sanitize_parameters(
            categories=categories,
            discover_urls_concurrency=discover_urls_concurrency,
            use_async=use_async)

        categories = sanitized_parameters['categories']
        discover_urls_concurrency = \
            sanitized_parameters['discover_urls_concurrency']
        use_async = sanitized_parameters['use_async']

        logger.info('Discovering URLs for: {}'.format(cls.__name__))

        discovered_urls_with_categories = []

        if use_async:
            category_chunks = chunks(
                categories, discover_urls_concurrency)

            for category_chunk in category_chunks:
                chunk_tasks = []

                logger.info('Discovering URLs for: {}'.format(
                    category_chunk))

                for category in category_chunk:
                    task = cls.discover_urls_for_category_task.s(
                        cls.__name__, category, extra_args)
                    task.set(queue='storescraper_discover_urls_for_category')
                    chunk_tasks.append(task)
                tasks_group = cls.create_celery_group(chunk_tasks)

                # Prevents Celery error for running a task inside another
                with allow_join_result():
                    task_results = tasks_group.get()

                for idx, task_result in enumerate(task_results):
                    category = category_chunk[idx]
                    logger.info('Discovered URLs for {}:'.format(category))
                    for discovered_url in task_result:
                        logger.info(discovered_url)
                        discovered_urls_with_categories.append({
                            'url': discovered_url,
                            'category': category
                        })
        else:
            logger.info('Using sync method')
            for category in categories:
                for url in cls.discover_urls_for_category(
                        category, extra_args):
                    logger.info('Discovered URL: {} ({})'.format(
                        url, category))
                    discovered_urls_with_categories.append({
                        'url': url,
                        'category': category
                    })

        return discovered_urls_with_categories

    @classmethod
    def products_for_urls(cls, discovery_urls_with_categories, extra_args=None,
                          products_for_url_concurrency=None,
                          use_async=True):
        sanitized_parameters = cls.sanitize_parameters(
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async)

        products_for_url_concurrency = \
            sanitized_parameters['products_for_url_concurrency']
        use_async = sanitized_parameters['use_async']

        logger.info('Retrieving products for: {}'.format(cls.__name__))

        for entry in discovery_urls_with_categories:
            logger.info('{} ({})'.format(entry['url'], entry['category']))

        products = []
        discovery_urls_without_products = []

        if use_async:
            discovery_urls_with_categories_chunks = chunks(
                discovery_urls_with_categories, products_for_url_concurrency)

            task_counter = 1
            for discovery_urls_with_categories_chunk in \
                    discovery_urls_with_categories_chunks:
                chunk_tasks = []

                for discovered_url_entry in \
                        discovery_urls_with_categories_chunk:
                    logger.info('Retrieving URL ({} / {}): {}'.format(
                        task_counter, len(discovery_urls_with_categories),
                        discovered_url_entry['url']))
                    task = cls.products_for_url_task.s(
                        cls.__name__, discovered_url_entry['url'],
                        discovered_url_entry['category'], extra_args)
                    task.set(queue='storescraper_products_for_url')
                    chunk_tasks.append(task)
                    task_counter += 1

                tasks_group = cls.create_celery_group(chunk_tasks)

                # Prevents Celery error for running a task inside another
                with allow_join_result():
                    task_results = tasks_group.get()

                for idx, task_result in enumerate(task_results):
                    for serialized_product in task_result:
                        product = Product.deserialize(serialized_product)
                        logger.info('{}\n'.format(product))
                        products.append(product)

                    if not task_result:
                        discovery_urls_without_products.append(
                            discovery_urls_with_categories_chunk[idx]['url'])
        else:
            logger.info('Using sync method')
            for discovered_url_entry in discovery_urls_with_categories:
                retrieved_products = cls.products_for_url(
                    discovered_url_entry['url'],
                    discovered_url_entry['category'],
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
    def discover_urls_for_category_task(store_class_name, category,
                                        extra_args=None):
        store = get_store_class_by_name(store_class_name)
        logger.info('Discovering URLs')
        logger.info('Store: ' + store.__name__)
        logger.info('Category: ' + category)
        try:
            discovered_urls = store.discover_urls_for_category(
                category, extra_args)
        except Exception:
            error_message = 'Error discovering URLs from {}: {} - {}'.format(
                store_class_name,
                category,
                traceback.format_exc())
            logger.error(error_message)
            raise StoreScrapError(error_message)

        for idx, url in enumerate(discovered_urls):
            logger.info('{} - {}'.format(idx, url))
        return discovered_urls

    @staticmethod
    @shared_task
    def products_for_url_task(store_class_name, url, category=None,
                              extra_args=None):
        store = get_store_class_by_name(store_class_name)
        logger.info('Obtaining products for URL')
        logger.info('Store: ' + store.__name__)
        logger.info('Category: ' + category)
        logger.info('URL: ' + url)

        try:
            raw_products = store.products_for_url(
                url, category, extra_args)
        except Exception:
            error_message = 'Error retrieving products from {}: {} - {}' \
                            ''.format(store_class_name, url,
                                      traceback.format_exc())
            logger.error(error_message)
            raise StoreScrapError(error_message)

        serialized_products = [p.serialize() for p in raw_products]

        for idx, product in enumerate(serialized_products):
            logger.info('{} - {}'.format(idx, product))

        return serialized_products

    @staticmethod
    @shared_task
    def products_task(store_class_name, categories=None, extra_args=None,
                      discover_urls_concurrency=None,
                      products_for_url_concurrency=None, use_async=None):
        store = get_store_class_by_name(store_class_name)
        result = store.products(
            categories=categories, extra_args=extra_args,
            discover_urls_concurrency=discover_urls_concurrency,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async)

        serialized_result = {
            'products': [p.serialize() for p in result['products']],
            'discovery_urls_without_products':
                result['discovery_urls_without_products']
        }

        return serialized_result

    @staticmethod
    @shared_task
    def products_for_urls_task(store_class_name,
                               discovery_urls_with_categories,
                               extra_args=None,
                               products_for_url_concurrency=None,
                               use_async=True):
        store = get_store_class_by_name(store_class_name)
        result = store.products_for_urls(
            discovery_urls_with_categories, extra_args=extra_args,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async)

        serialized_result = {
            'products': [p.serialize() for p in result['products']],
            'discovery_urls_without_products':
                result['discovery_urls_without_products']
        }

        return serialized_result

    ##########################################################################
    # Implementation dependant methods
    ##########################################################################

    @classmethod
    def categories(cls):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
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

    @classmethod
    def sanitize_parameters(cls, categories=None,
                            discover_urls_concurrency=None,
                            products_for_url_concurrency=None, use_async=None):
        if categories is None:
            categories = cls.categories()
        else:
            categories = [category for category in cls.categories()
                          if category in categories]

        if discover_urls_concurrency is None:
            discover_urls_concurrency = cls.preferred_discover_urls_concurrency

        if products_for_url_concurrency is None:
            products_for_url_concurrency = \
                cls.preferred_products_for_url_concurrency

        if use_async is None:
            use_async = cls.prefer_async

        return {
            'categories': categories,
            'discover_urls_concurrency': discover_urls_concurrency,
            'products_for_url_concurrency': products_for_url_concurrency,
            'use_async': use_async,
        }
