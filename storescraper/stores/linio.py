import json
import logging
import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    session_with_proxy,
    html_to_markdown,
    check_ean13,
    remove_words,
)


class Linio(Store):
    base_domain = "https://www.linio.com"
    currency = property(lambda self: NotImplementedError())

    @classmethod
    def _category_paths(cls):
        raise NotImplementedError(
            "This method must be implemented by " "subclasses of Linio"
        )

    @classmethod
    def categories(cls):
        category_paths = cls._category_paths()
        return list(set(e[1] for e in category_paths))

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = cls._category_paths()

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )

        sortings = ["relevance", "price_asc", "price_desc"]

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            for sorting in sortings:
                page = 1

                while True:
                    category_url = (
                        "{}/c/{}?is_international=0&sortBy={}"
                        "&page={}".format(cls.base_domain, category_path, sorting, page)
                    )
                    print(category_url)

                    if page >= 40:
                        raise Exception("Page overflow: " + category_url)

                    soup = BeautifulSoup(session.get(category_url).text, "lxml")

                    products_containers = soup.findAll("div", "catalogue-product")

                    if not products_containers:
                        if page == 1:
                            logging.warning("Empty category: " + category_url)
                        break

                    for product_container in products_containers:
                        if product_container.find(
                            "div", "badge-international-shipping"
                        ):
                            continue

                        product_url = (
                            cls.base_domain + product_container.find("a")["href"]
                        )

                        product_url = product_url.split("?")[0]
                        product_urls.append(product_url)

                    page += 1

        return list(set(product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        response = session.get(url)

        if response.status_code in [404, 500] or response.url != url:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        key = re.search(r"-([a-zA-Z0-9]+)$", url).groups()[0]
        page_source = response.text
        pricing_str = re.search(
            r"window.dataLayer.push\(([\S\s]+?)\);\n", page_source
        ).groups()[0]
        pricing_data = json.loads(pricing_str)

        name = pricing_data["product_name"][:250]
        sku = pricing_data["sku_config"]

        reference_code = pricing_data["ean_code"].strip()
        ean = None

        if check_ean13(reference_code):
            ean = reference_code
        else:
            name = "{} - {}".format(name, reference_code)

        name = name[0:256]

        normal_price = Decimal(str(pricing_data["special_price"]))

        pricing_container = soup.find("div", "product-price-lg")

        if not soup.find("span", "sprite-cmr"):
            offer_price = normal_price
        else:
            offer_price_container = pricing_container.find("span", "price-promotional")

            if offer_price_container:
                offer_price = Decimal(remove_words(offer_price_container.text))
                if offer_price > normal_price:
                    offer_price = normal_price
            else:
                offer_price = normal_price

        if normal_price == Decimal(9999999) or offer_price == Decimal(9999999):
            return []

        soup = BeautifulSoup(page_source, "lxml")

        condition_dict = {
            "Nuevo": "https://schema.org/NewCondition",
            "Reacondicionado": "https://schema.org/RefurbishedCondition",
        }

        condition_label = soup.find("span", "badge-condition-type")

        if condition_label:
            condition = condition_dict[condition_label.text.strip()]
        else:
            condition = "https://schema.org/NewCondition"

        description = html_to_markdown(str(soup.find("div", "feature-information")))

        description += "\n\n" + html_to_markdown(
            str(soup.find("div", "features-box-section"))
        )

        picture_urls = [
            "https:" + tag.find("img")["data-lazy"]
            for tag in soup.findAll("div", {"id": "image-product"})
        ]

        availability_container = soup.find("link", {"itemprop": "availability"})

        if not availability_container:
            stock = 0
        elif soup.find("div", "product-title").find(
            "span", "badge-pill-international-shipping"
        ):
            stock = 0
            description = "ST-INTERNATIONAL-SHIPPING {}".format(description)
        elif availability_container["href"] == "https://schema.org/InStock":
            stock = -1
        else:
            stock = 0

        seller_container = soup.find("div", "seller-name-rating-section")
        if seller_container:
            seller = seller_container.text.strip()
        else:
            seller = None

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            cls.currency,
            sku=sku,
            ean=ean,
            description=description,
            picture_urls=picture_urls,
            condition=condition,
            seller=seller,
        )

        return [p]
