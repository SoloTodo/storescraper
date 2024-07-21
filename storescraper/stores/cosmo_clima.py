import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import AIR_CONDITIONER


class CosmoClima(StoreWithUrlExtensions):
    # ONLY CONSIDERS LG PRODUCTS

    url_extensions = [
        [
            "aire-acondicionado/aire-acondicionado-residencial/split-muro-multisplit-anwo-clark-hisense-samsung-"
            "kendal-lg-airolite-splendid-fujitsu-9000-12000-18000-24000-btu?filter[cfv][42869][]=117715",
            AIR_CONDITIONER,
        ],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        product_urls = []
        session = session_with_proxy(extra_args)
        page = 1

        while True:
            if page > 10:
                raise Exception("Page overflow")

            url = "https://www.cosmoclima.cl/{}&page={}".format(url_extension, page)
            print(url)
            response = session.get(url)

            soup = BeautifulSoup(response.text, "lxml")
            products = soup.findAll("div", "product-block")

            if not products:
                break

            for product in products:
                product_url = "https://www.cosmoclima.cl" + product.find("a")["href"]
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, "lxml")

        buy_form_tag = soup.find("form", "product-form")

        if not buy_form_tag:
            return []

        key = buy_form_tag["data-id"]
        sku_tag = soup.find("span", "product-heading__sku")
        sku = sku_tag.text.replace("SKU:", "").strip()
        product_data = json.loads(
            soup.find("script", {"type": "application/ld+json"}).text
        )

        name = product_data["name"]
        if product_data["offers"]["availability"] == "http://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        price = Decimal(product_data["offers"]["price"].replace(".", ""))
        picture_urls = [product_data["image"]]

        description = html_to_markdown(str(soup.find("ul", "product-accordion__list")))

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
            "CLP",
            sku=sku,
            part_number=sku,
            description=description,
            picture_urls=picture_urls,
        )

        return [p]
