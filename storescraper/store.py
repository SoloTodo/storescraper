import logging
import logstash
import time
import traceback
import uuid
from collections import defaultdict, OrderedDict

from celery import chain, group, shared_task
from celery.result import allow_join_result
from celery.utils.log import get_task_logger
from elasticsearch import Elasticsearch

from datetime import datetime, timezone

from .product import Product
from .utils import get_store_class_by_name, chunks
import redis

logger = get_task_logger(__name__)

ES = Elasticsearch(
    "https://localhost:9200",
    ca_certs="http_ca.crt",
    http_auth=("elastic", "Mo+2hdOYBpIJi4NYG*KL"),
)
logging.getLogger("elastic_transport").setLevel(logging.WARNING)

logstash_logger = logging.getLogger("python-logstash-logger")
logstash_logger.setLevel(logging.INFO)
logstash_logger.addHandler(logstash.TCPLogstashHandler("localhost", 5959))

redis_client = redis.StrictRedis(
    host="localhost",
    port=6379,
    db=0,
)


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
    def products(
        cls,
        categories=None,
        extra_args=None,
        discover_urls_concurrency=None,
        products_for_url_concurrency=None,
        use_async=None,
    ):
        sanitized_parameters = cls.sanitize_parameters(
            categories=categories,
            discover_urls_concurrency=discover_urls_concurrency,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async,
        )

        categories = sanitized_parameters["categories"]
        discover_urls_concurrency = sanitized_parameters["discover_urls_concurrency"]
        products_for_url_concurrency = sanitized_parameters[
            "products_for_url_concurrency"
        ]
        use_async = sanitized_parameters["use_async"]

        logger.info("Obtaining products from: {}".format(cls.__name__))
        logger.info("Categories: {}".format(", ".join(categories)))

        extra_args = cls._extra_args_with_preflight(extra_args)

        discovered_entries = cls.discover_entries_for_categories(
            categories=categories,
            extra_args=extra_args,
            discover_urls_concurrency=discover_urls_concurrency,
            use_async=use_async,
        )

        return cls.products_for_urls(
            discovered_entries,
            extra_args=extra_args,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async,
        )

    @classmethod
    def products_for_keyword(
        cls,
        keyword,
        threshold,
        extra_args=None,
        products_for_url_concurrency=None,
        use_async=None,
    ):

        sanitized_parameters = cls.sanitize_parameters(
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async,
        )

        products_for_url_concurrency = sanitized_parameters[
            "products_for_url_concurrency"
        ]
        use_async = sanitized_parameters["use_async"]

        extra_args = cls._extra_args_with_preflight(extra_args)

        product_urls = cls.discover_urls_for_keyword(keyword, threshold, extra_args)

        product_entries = OrderedDict()

        for url in product_urls:
            product_entries[url] = {
                "positions": [],
                "category": None,
            }

        if extra_args is None:
            extra_args = {}

        extra_args["source"] = "keyword_search"

        return cls.products_for_urls(
            product_entries,
            extra_args=extra_args,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async,
        )

    @classmethod
    def discover_entries_for_categories_non_blocker(
        cls,
        categories=None,
        extra_args=None,
        discover_urls_concurrency=None,
        scrape_products=True,
    ):
        sanitized_parameters = cls.sanitize_parameters(
            categories=categories, discover_urls_concurrency=discover_urls_concurrency
        )

        categories = sanitized_parameters["categories"]
        discover_urls_concurrency = sanitized_parameters["discover_urls_concurrency"]
        extra_args = cls._extra_args_with_preflight(extra_args)
        process_id = str(uuid.uuid4())

        print(f"Process ID: {process_id}")
        print(f"Discovering URLs for: {cls.__name__}")

        extra_args["process_id"] = process_id
        category_chunks = chunks(categories, discover_urls_concurrency)
        task_group = []

        for category_chunk in category_chunks:
            chunk_tasks = []

            for category in category_chunk:
                task = cls.discover_entries_for_category_task.si(
                    cls.__name__, category, extra_args
                ).set(queue="storescraper")

                if scrape_products:
                    task = chain(
                        task,
                        cls.products_for_urls_task_non_blocker.s(
                            store_class_name=cls.__name__,
                            category=category,
                            extra_args=extra_args,
                        ).set(queue="storescraper"),
                    )

                chunk_tasks.append(task)

            task_group.append(group(*chunk_tasks))

        task_group.append(
            cls.finish_process.si(cls.__name__, process_id).set(queue="storescraper")
        )

        # for i in range(len(task_group) - 1):
        #    task_group[i].link(task_group[i + 1])

        # task_group[0].apply_async()

        chain(cls.nothing.si().set(queue="storescraper"), *task_group).apply_async()

        cls.fetch_es_url_logs(process_id)

    @shared_task()
    def nothing():
        pass

    def fetch_redis_data(cls, process_id):
        while True:
            url_count = redis_client.llen(f"{process_id}_urls")
            print(f"Discovered URLs: {url_count}")

            if redis_client.exists(f"{process_id}_urls_finished"):
                print(f"Process {process_id} finished: {url_count} URLs discovered")
                return

            time.sleep(5)

    @classmethod
    def fetch_es_url_logs(cls, process_id, include_category_counts=False):
        products_count = 0
        urls_count = 0
        categories = {}
        current_time = datetime.now(timezone.utc)
        timestamp = None

        while True:
            query = {
                "size": 1000,
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"@fields.process_id": process_id}},
                            {"range": {"@timestamp": {"gt": timestamp}}},
                        ]
                    }
                },
                "sort": [{"@timestamp": {"order": "asc"}}],
            }

            response = ES.search(index="logs-test", body=query)

            for hit in response["hits"]["hits"]:
                if "product" in hit["_source"]["@fields"]:
                    products_count += 1
                elif "url" in hit["_source"]["@fields"]:
                    urls_count += 1

                    if include_category_counts:
                        category = hit["_source"]["@fields"]["category"]
                        categories[category] = categories.get(category, 0) + 1

                if hit["_source"]["@message"] == f"{cls.__name__}: process finished":
                    print(
                        f"\n\n{cls.__name__} process {process_id} finished with {urls_count} URLs"
                    )

                    if include_category_counts:
                        print("-" * 80)

                        for category in categories:
                            print(f"{category}: {categories[category]}")

                        print("\n")

                    return

                timestamp = hit["_source"]["@timestamp"]

            print(f"Discovered URLs: {urls_count} | Scraped products: {products_count}")

            time.sleep(10)

    @classmethod
    def discover_entries_for_categories(
        cls,
        categories=None,
        extra_args=None,
        discover_urls_concurrency=None,
        use_async=True,
    ):
        sanitized_parameters = cls.sanitize_parameters(
            categories=categories,
            discover_urls_concurrency=discover_urls_concurrency,
            use_async=use_async,
        )

        categories = sanitized_parameters["categories"]
        discover_urls_concurrency = sanitized_parameters["discover_urls_concurrency"]
        use_async = sanitized_parameters["use_async"]

        logger.info("Discovering URLs for: {}".format(cls.__name__))

        entry_positions = defaultdict(lambda: list())
        url_category_weights = defaultdict(lambda: defaultdict(lambda: 0))
        extra_args = cls._extra_args_with_preflight(extra_args)
        count = 0
        if use_async:
            category_chunks = chunks(categories, discover_urls_concurrency)

            for category_chunk in category_chunks:
                chunk_tasks = []

                logger.info("Discovering URLs for: {}".format(category_chunk))

                for category in category_chunk:
                    task = cls.discover_entries_for_category_task.s(
                        cls.__name__, category, extra_args
                    )
                    task.set(queue="storescraper")
                    chunk_tasks.append(task)
                tasks_group = cls.create_celery_group(chunk_tasks)

                # Prevents Celery error for running a task inside another
                with allow_join_result():
                    task_results = tasks_group.get()

                for idx, task_result in enumerate(task_results):
                    category = category_chunk[idx]
                    logger.info("Discovered URLs for {}:".format(category))
                    for url, positions in task_result.items():
                        logger.info(url)
                        logger.info(positions)

                        if positions:
                            for pos in positions:
                                entry_positions[url].append(
                                    (pos["section_name"], pos["value"])
                                )
                                url_category_weights[url][category] += pos[
                                    "category_weight"
                                ]
                        else:
                            # Legacy for implementations without position data
                            url_category_weights[url][category] = 1
                            entry_positions[url] = []
        else:
            logger.info("Using sync method")
            for category in categories:
                for url, positions in cls.discover_entries_for_category(
                    category, extra_args
                ).items():
                    count += 1
                    url_category_weights[url][category] = 1
                    entry_positions[url] = []
        print(len(entry_positions), count)
        exit()
        discovered_entries = {}
        for url, positions in entry_positions.items():
            category, max_weight = max(
                url_category_weights[url].items(),
                key=lambda x: x[1],
            )

            # Only include the url in the discovery set if it appears in a
            # weighted section, for example generic "Electrodomésticos"
            # section have 0 weight, but specific sections
            # (e.g. "Refrigeradores") have positive values. This allows us to
            # map generic sections positioning without considering their
            # products if they don't appear in a specifically mapped
            # relevant section

            discovered_entries[url] = {
                "positions": positions,
                "category": category,
                "category_weight": 1,
            }

        return discovered_entries

    @classmethod
    def products_for_urls(
        cls,
        discovered_entries,
        extra_args=None,
        products_for_url_concurrency=None,
        use_async=True,
    ):
        sanitized_parameters = cls.sanitize_parameters(
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async,
        )

        products_for_url_concurrency = sanitized_parameters[
            "products_for_url_concurrency"
        ]
        use_async = sanitized_parameters["use_async"]

        logger.info("Retrieving products for: {}".format(cls.__name__))
        logger.info(discovered_entries)

        for url, entry_metadata in discovered_entries.items():
            logger.info("{} ({})".format(url, entry_metadata["category"]))

        products = []
        discovery_urls_without_products = []
        extra_args = cls._extra_args_with_preflight(extra_args)

        if use_async:
            discovery_entries_chunks = chunks(
                list(discovered_entries.items()), products_for_url_concurrency
            )

            task_counter = 1
            for discovery_entries_chunk in discovery_entries_chunks:
                chunk_tasks = []

                for entry_url, entry_metadata in discovery_entries_chunk:
                    logger.info(
                        "Retrieving URL ({} / {}): {}".format(
                            task_counter, len(discovered_entries), entry_url
                        )
                    )
                    task = cls.products_for_url_task.s(
                        cls.__name__, entry_url, entry_metadata["category"], extra_args
                    )
                    task.set(queue="storescraper")
                    chunk_tasks.append(task)
                    task_counter += 1

                tasks_group = cls.create_celery_group(chunk_tasks)

                # Prevents Celery error for running a task inside another
                with allow_join_result():
                    task_results = tasks_group.get()

                for idx, task_result in enumerate(task_results):
                    for serialized_product in task_result:
                        product = Product.deserialize(serialized_product)
                        if not product.positions:
                            product.positions = discovery_entries_chunk[idx][1][
                                "positions"
                            ]

                        logger.info("{}\n".format(product))
                        products.append(product)

                    if not task_result:
                        discovery_urls_without_products.append(
                            discovery_entries_chunk[idx][0]
                        )
        else:
            logger.info("Using sync method")
            for entry_url, entry_metadata in discovered_entries.items():
                retrieved_products = cls.products_for_url(
                    entry_url, entry_metadata["category"], extra_args
                )

                for product in retrieved_products:
                    if not product.positions:
                        product.positions = entry_metadata["positions"]
                    logger.info("{}\n".format(product))
                    products.append(product)

                if not retrieved_products:
                    discovery_urls_without_products.append(entry_url)

        return {
            "products": products,
            "discovery_urls_without_products": discovery_urls_without_products,
        }

    ##########################################################################
    # Celery tasks wrappers
    ##########################################################################

    @staticmethod
    @shared_task()
    def finish_process(store, process_id):
        time.sleep(10)
        redis_client.rpush(f"{process_id}_urls_finished", "finished")
        logstash_logger.info(
            f"{store}: process finished",
            extra={"process_id": process_id},
        )

    @staticmethod
    @shared_task()
    def discover_entries_for_category_task(store_class_name, category, extra_args=None):
        store = get_store_class_by_name(store_class_name)
        logger.info("Discovering URLs")
        logger.info("Store: " + store.__name__)
        logger.info("Category: " + category)

        process_id = extra_args.get("process_id", None)
        logger.info(f"Process ID: {process_id}")

        try:
            discovered_entries = store.discover_entries_for_category(
                category, extra_args
            )
        except Exception:
            error_message = "Error discovering URLs from {}: {} - {}".format(
                store_class_name, category, traceback.format_exc()
            )
            logger.error(error_message)
            raise StoreScrapError(error_message)

        for url in discovered_entries.keys():
            logger.info(url)
            logstash_logger.info(
                f"{store.__name__}: Discovered URL",
                extra={
                    "process_id": process_id or None,
                    "store": store.__name__,
                    "category": category,
                    "url": url,
                },
            )

        return discovered_entries

    @staticmethod
    @shared_task(autoretry_for=(StoreScrapError,), max_retries=5, default_retry_delay=5)
    def products_for_url_task(store_class_name, url, category=None, extra_args=None):
        store = get_store_class_by_name(store_class_name)
        """
        logger.info("Obtaining products for URL")
        logger.info("Store: " + store.__name__)
        logger.info("Category: {}".format(category))
        logger.info("URL: " + url)
        """

        try:
            raw_products = store.products_for_url(url, category, extra_args)
        except Exception:
            error_message = "Error retrieving products from {}: {} - {}" "".format(
                store_class_name, url, traceback.format_exc()
            )
            logger.error(error_message)
            raise StoreScrapError(error_message)

        serialized_products = [p.serialize() for p in raw_products]

        # for idx, product in enumerate(serialized_products):
        #    logger.info("{} - {}".format(idx, product))

        return serialized_products

    @staticmethod
    @shared_task(autoretry_for=(StoreScrapError,), max_retries=5, default_retry_delay=5)
    def products_for_urls_task(
        store_class_name,
        discovery_entries,
        extra_args=None,
        products_for_url_concurrency=None,
        use_async=True,
    ):
        store = get_store_class_by_name(store_class_name)
        result = store.products_for_urls(
            discovery_entries,
            extra_args=extra_args,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async,
        )

        serialized_result = {
            "products": [p.serialize() for p in result["products"]],
            "discovery_urls_without_products": result[
                "discovery_urls_without_products"
            ],
        }

        return serialized_result

    @staticmethod
    @shared_task(autoretry_for=(StoreScrapError,), max_retries=5, default_retry_delay=5)
    def products_for_urls_task_non_blocker(
        discovered_entries,
        store_class_name,
        category,
        products_for_url_concurrency=10,
        extra_args=None,
    ):
        store = get_store_class_by_name(store_class_name)
        # extra_args = cls._extra_args_with_preflight(extra_args)
        discovery_entries_chunks = chunks(list(discovered_entries.items()), 6)

        for discovery_entries_chunk in discovery_entries_chunks:
            chunk_tasks = []

            for entry_url, _ in discovery_entries_chunk:
                task = chain(
                    store.products_for_url_task.si(
                        store_class_name, entry_url, category, extra_args
                    ).set(queue="storescraper"),
                    store.log_product.s(
                        store_class_name=store_class_name,
                        category=category,
                        extra_args=extra_args,
                    ).set(queue="storescraper"),
                )

                chunk_tasks.append(task)

            tasks_group = group(chunk_tasks)
            tasks_group.apply_async()

    @shared_task()
    def log_product(product, store_class_name, category, extra_args):
        logstash_logger.info(
            f"{store_class_name}: Discovered product",
            extra={
                "process_id": extra_args["process_id"],
                "store": store_class_name,
                "category": category,
                "product": product,
            },
        )

    ##########################################################################
    # Implementation dependant methods
    ##########################################################################

    @classmethod
    def categories(cls):
        raise NotImplementedError(
            "This method must be implemented by " "subclasses of Store"
        )

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        raise NotImplementedError(
            "This method must be implemented by " "subclasses of Store"
        )

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        raise NotImplementedError(
            "This method must be implemented by " "subclasses of Store"
        )

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        raise NotImplementedError(
            "This method must be implemented by " "subclasses of Store"
        )

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        # If the concrete class does not implement it yet, call the old
        # discover_urls_for_category method and patch it
        urls = cls.discover_urls_for_category(category, extra_args)
        return {url: [] for url in urls}

    @classmethod
    def preflight(cls, extra_args=None):
        # Executes any logic that needs to be done only once per scraping
        # (e.g. obtaining session cookies). Should return a dictionary that
        # is merged with the "extra_args" available in the "discover" methods
        # above or products_for_url.
        return {}

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
    def sanitize_parameters(
        cls,
        categories=None,
        discover_urls_concurrency=None,
        products_for_url_concurrency=None,
        use_async=None,
    ):
        if categories is None:
            categories = cls.categories()
        else:
            categories = [
                category for category in cls.categories() if category in categories
            ]

        if discover_urls_concurrency is None:
            discover_urls_concurrency = cls.preferred_discover_urls_concurrency

        if products_for_url_concurrency is None:
            products_for_url_concurrency = cls.preferred_products_for_url_concurrency

        if use_async is None:
            use_async = cls.prefer_async

        return {
            "categories": categories,
            "discover_urls_concurrency": discover_urls_concurrency,
            "products_for_url_concurrency": products_for_url_concurrency,
            "use_async": use_async,
        }

    ######################################################################
    # Private methods
    ######################################################################

    @classmethod
    def _extra_args_with_preflight(cls, extra_args=None):
        # Merges the extra_args with the preflight args and prevents
        # preflight from being called twice unnecesarily

        # If the preflight args have already been calculated, return
        if extra_args is not None and "preflight_done" in extra_args:
            return extra_args

        preflight_args = {"preflight_done": True}
        preflight_args.update(cls.preflight(extra_args))
        if extra_args is not None:
            preflight_args.update(extra_args)

        return preflight_args
