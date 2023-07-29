from .store import Store


class StoreWithUrlExtensions(Store):
    url_extensions = []

    @classmethod
    def categories(cls):
        cats = []
        for _category_path, category in cls.url_extensions:
            if category not in cats:
                cats.append(category)
        return cats

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []

        for url_extension, local_category in cls.url_extensions:
            if local_category != category:
                continue

            local_urls = cls.discover_urls_for_url_extension(
                url_extension, extra_args)

            for local_url in local_urls:
                if local_url not in product_urls:
                    product_urls.append(local_url)

        return product_urls

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        raise NotImplementedError('This method must be provided by subclasses')
