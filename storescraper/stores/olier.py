import json
from decimal import Decimal
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Olier(Store):
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
            url = "https://www.olier.com.py/get-productos?page={}&marcas=44" "".format(
                page
            )

            if page >= 15:
                raise Exception("Page overflow: " + url)

            print(url)

            data = session.get(url).text
            product_containers = json.loads(data)["paginacion"]["data"]

            if len(product_containers) == 0:
                if page == 1:
                    raise Exception("Empty site")
                break

            for product in product_containers:
                product_urls.append(product["url_ver"])

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, "lxml")
        product_id = soup.find("span", "product-cod").text.replace("SKU: ", "")
        endpoint = "https://www.olier.com.py/get-productos?query_string={}" "".format(
            product_id
        )
        product_entries = session.get(endpoint).json()

        for entry in product_entries["paginacion"]["data"]:
            if entry["codigo_articulo"] == product_id:
                product_entry = entry
                break
        else:
            raise Exception("No product found")

        name = product_entry["nombre"]
        if not name:
            name = product_entry["producto"]["nombre"]
        sku = product_entry["codigo_articulo"]
        ean = product_entry.get("ean", None)
        url_ver = product_entry["url_ver"]
        price = Decimal(product_entry["precio_retail"])
        stock = product_entry["existencia"]
        description = html_to_markdown(product_entry["producto"]["descripcion"] or "")
        picture_urls = []
        for i in product_entry["imagenes"]:
            if i["url_imagen"]:
                picture_urls.append(
                    "https://www.olier.com.py/storage/sku/" + i["url_imagen"]
                )

        p = Product(
            name,
            cls.__name__,
            category,
            url_ver,
            url_ver,
            sku,
            stock,
            price,
            price,
            "PYG",
            sku=sku,
            ean=ean,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
