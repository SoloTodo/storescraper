import logging
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.stores.mercado_libre_chile import MercadoLibreChile
from ..utils import session_with_proxy


class MercadoLibreColombiaLg(MercadoLibreChile):
    official_store_id = 1043
    # price_accuracy = "0.01"

    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1
        while True:
            if page > 10:
                raise Exception("Page overflow")
            index = str(50 * (page - 1) + 1)
            url_webpage = (
                "https://listado.mercadolibre.com.co/"
                "_Desde_{}_Tienda_lg-electronics-colombia_NoIndex_True".format(index)
            )
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("li", "ui-search-layout__item")
            if not product_containers:
                if page == 1:
                    logging.warning("Empty category")
                break
            for container in product_containers:
                product_url = container.find("a")["href"].split("#")[0].split("?")[0]
                product_url += "?pdp_filters=official_store:{}".format(
                    cls.official_store_id
                )
                product_urls.append(product_url)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        # Remove the seller because we consider MecadoLibrePeruLg to be a
        # standalone retailer, in particular because the LG WTB system
        # only displays entries without a seller (not from marketplaces)
        # and we want to consider MercadoLibrePeruLG for that.
        products = super().products_for_url(
            url, category=category, extra_args=extra_args
        )

        filtered_products = []

        for product in products:
            assert product.seller
            product.seller = None
            product.currency = "COP"
            filtered_products.append(product)

        return filtered_products
