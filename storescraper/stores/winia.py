from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import OVEN, REFRIGERATOR, WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Winia(Store):
    @classmethod
    def categories(cls):
        return [REFRIGERATOR, WASHING_MACHINE, OVEN]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ["14-refrigeracion", REFRIGERATOR],
            ["22-carga-frontal", WASHING_MACHINE],
            ["21-carga-superior", WASHING_MACHINE],
            ["23-secadoras", WASHING_MACHINE],
            ["24-microondas", OVEN],
        ]

        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = "curl/7.54.0"
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception("Page overflow: " + url_extension)
                url_webpage = "https://www.winia.cl/{}?" "page={}".format(
                    url_extension, page
                )
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")
                product_containers = soup.findAll("article", "product-miniature")
                if not product_containers:
                    if page == 1:
                        logging.warning("Empty category: " + url_extension)
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
        session.headers["User-Agent"] = "curl/7.54.0"
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        key = soup.find("input", {"id": "product_page_product_id"})["value"]
        name = soup.find("h1", "page-title").text.strip()
        sku = soup.find("div", "product-reference").find("span").text.strip()

        price_span = soup.find("span", "product-price")
        if not price_span:
            return []
        price = Decimal(price_span["content"])

        add_button = soup.find("button", {"data-button-action": "add-to-cart"})
        if add_button and "disabled" not in add_button.attrs:
            stock_div = soup.find("div", "product-quantities")
            if stock_div:
                stock = int(stock_div.find("span")["data-stock"])
            else:
                stock = -1
        else:
            stock = 0

        pictures_container = soup.find("div", {"id", "product-images-large"})
        picture_urls = []
        for i in pictures_container.findAll("a"):
            picture_urls.append(i["href"])

        description = html_to_markdown(str(soup.find("div", "product-description")))

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
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
