import json
import re

from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    session_with_proxy,
    html_to_markdown,
)
from storescraper.categories import TELEVISION


class PlazaLama(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only interested in LG products

        session = session_with_proxy(extra_args)
        product_urls = []

        if TELEVISION != category:
            return []

        payload = {
            "operationName": "SearchProducts",
            "variables": {
                "searchProductsInput": {
                    "clientId": "PLAZA_LAMA",
                    "storeReference": "PL08-D",
                    "currentPage": 0,
                    "minScore": 1,
                    "pageSize": 200,
                    "search": [{"query": "lg"}],
                }
            },
            "query": "fragment CatalogProductModel on CatalogProductModel {slug __typename}"
            "query SearchProducts($searchProductsInput: SearchProductsInput!) {searchProducts(searchProductsInput: $searchProductsInput) {products {...CatalogProductModel __typename} __typename}}",
        }
        headers = {
            "Content-Type": "application/json",
        }
        page = 1

        while True:
            if page >= 30:
                raise Exception("Page overflow")

            payload["variables"]["searchProductsInput"]["currentPage"] = page
            url = "https://nextgentheadless.instaleap.io/api/v3"
            response = json.loads(session.post(url, json=payload, headers=headers).text)
            products = response["data"]["searchProducts"]["products"]

            if products == []:
                break

            for product in products:
                product_urls.append(f"https://plazalama.com.do/p/{product['slug']}")

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        sku = re.search(r"-(\d+)$", url).group(1)

        payload = {
            "operationName": "GetProductsBySKU",
            "variables": {
                "getProductsBySkuInput": {
                    "clientId": "PLAZA_LAMA",
                    "skus": [sku],
                    "storeReference": "PL08-D",
                }
            },
            "query": "fragment CatalogProductModel on CatalogProductModel {name isAvailable price photosUrl description __typename}"
            "query GetProductsBySKU($getProductsBySkuInput: GetProductsBySKUInput!) {getProductsBySKU(getProductsBySKUInput: $getProductsBySkuInput) {...CatalogProductModel __typename}}",
        }
        headers = {
            "Content-Type": "application/json",
        }
        session = session_with_proxy(extra_args)
        response = json.loads(
            session.post(
                "https://nextgentheadless.instaleap.io/api/v3",
                json=payload,
                headers=headers,
            ).text
        )
        product_response = response["data"]["getProductsBySKU"]

        assert len(product_response) == 1

        product = product_response[0]
        name = product["name"]
        stock = -1 if product["isAvailable"] else 0
        price = Decimal(product["price"])
        picture_urls = product["photosUrl"]
        description = html_to_markdown(product["description"])

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
            "DOP",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
