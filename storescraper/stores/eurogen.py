import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import REFRIGERATOR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Eurogen(Store):
    @classmethod
    def categories(cls):
        return [REFRIGERATOR]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [REFRIGERATOR]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = "https://eurogen.com.uy/index_search.php"
            data = session.post(url_webpage, {"txtbuscar": "lg"}).text
            soup = BeautifulSoup(data, "lxml")
            product_containers = soup.findAll("form", {"id": "form1"})
            if not product_containers:
                break
            for container in product_containers:
                product_url = container.find("input")["value"]
                product_urls.append(
                    "https://eurogen.com.uy/detalles.php?id=" + product_url
                )
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        info_container = soup.find("div", "product-information")
        name = info_container.find("p").text
        if "LG" not in name.upper():
            return []
        sku = soup.find("input", {"name": "prod"})["value"]
        stock = -1
        price = Decimal(remove_words(info_container.findAll("bdi")[1].text))
        picture_urls = [
            "https://eurogen.com.uy/" + urllib.parse.quote(tag["src"])
            for tag in soup.find("div", "carousel-inner").findAll("img")
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
            "UYU",
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
