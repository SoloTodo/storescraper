from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.utils import session_with_proxy
from .mercado_libre_chile import MercadoLibreChile


class Tecnoplaza(MercadoLibreChile):
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
            url_webpage = "https://www.tecnoplaza.com.co/listado/_BRAND_215_Desde_{}_NoIndex_True".format(
                index
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "html.parser")
            product_containers = soup.findAll("li", "ui-search-layout__item")
            if not product_containers:
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
        products = cls._products_for_url_with_custom_price(
            url, category=category, extra_args=extra_args
        )

        for product in products:
            product.store = cls.__name__
            product.currency = "COP"

        return products
