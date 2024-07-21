import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Electrocol(Store):
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
            url = (
                "https://electrocol.com/index.php?fc=module&module=leoproductsearch&controller=productsearch"
                "&search_query=LG&page={}"
            ).format(page)
            print(url)
            res = session.get(url)
            soup = BeautifulSoup(res.text, "lxml")
            product_containers = soup.findAll("div", "ajax_block_product")
            if not product_containers:
                break

            for product in product_containers:
                brand_name = product.find("p", "marca-producto").text.strip()
                if brand_name != "LG":
                    continue
                product_url = product.find("a")["href"]
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        json_data = json.loads(
            soup.find("div", {"id": "product-details"})["data-product"]
        )

        key = str(json_data["id_product"])
        sku = json_data["reference"]
        name = json_data["name"]
        description = html_to_markdown(json_data["description"])
        stock = json_data["quantity"]
        price = Decimal(json_data["price_amount"])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            "COP",
            sku=sku,
            description=description,
            part_number=sku,
        )
        return [p]
