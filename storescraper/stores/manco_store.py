import logging

from bs4 import BeautifulSoup

from storescraper.categories import VIDEO_CARD
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class MancoStore(StoreWithUrlExtensions):
    url_extensions = [
        ["computacion", VIDEO_CARD],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow: " + url_extension)
            index = str(50 * (page - 1) + 1)
            url_webpage = (
                "https://www.mancostore.cl/listado/"
                "{}/_Desde_{}_NoIndex_True".format(url_extension, index)
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("li", "ui-search-layout__item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category: " + url_extension)
                break
            for container in product_containers:
                product_url = (
                    container.find("a", "ui-search-link")["href"]
                    .split("#")[0]
                    .split("?")[0]
                )
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        from .mercado_libre_chile import MercadoLibreChile

        return MercadoLibreChile._products_for_url_with_custom_price(
            url, category=category, extra_args=extra_args
        )
