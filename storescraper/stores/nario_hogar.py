import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class NarioHogar(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [TELEVISION]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue

            page = 0
            while True:
                url_webpage = (
                    "https://www.nariohogar.com.uy/productos/"
                    "paginado?marcas=lg8&p={}".format(page)
                )
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")

                if "No se encontraron resultados" in soup.text:
                    if page == 0:
                        logging.warning("Empty category: " + local_category)
                    break

                product_containers = soup.findAll("div", "product-card-5")
                if not product_containers:
                    break
                for container in product_containers:
                    product_url = container.find("a")["href"]
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("meta", {"property": "og:title"})["content"]
        sku = url.split("/")[-1][:45]
        stock = -1
        price = Decimal(soup.find("div", "product-price").find("span").text.split()[-1])
        picture_urls = [
            urllib.parse.quote(tag["src"], safe="/:")
            for tag in soup.find("div", "swiper_gallery").findAll("img")
        ]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            "USD",
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
