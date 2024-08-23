from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    session_with_proxy,
    html_to_markdown,
    magento_picture_urls,
)
from storescraper.categories import TELEVISION


class LaCuracaoOnline(Store):
    country = ""
    currency = ""
    currency_iso = ""

    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def format_url(cls, page):
        return f"https://www.lacuracaonline.com/{cls.country}/catalogsearch/result/index/?marca=42974&p={page}&q=lg"

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # KEEPS ONLY LG PRODUCTS

        session = session_with_proxy(extra_args)
        product_urls = []

        if category != TELEVISION:
            return []

        page = 1

        while True:
            if page >= 15:
                raise Exception("Page overflow")

            url = cls.format_url(page)
            print(url)

            response = session.get(url)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "product")

            if not product_containers:
                if page == 1:
                    raise Exception("Empty section: {}".format(url))
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

        for i in range(5):
            response = session.get(url)

            if response.status_code == 404:
                return []

            if response.status_code == 200:
                break
        else:
            # Called if no "break" was executed
            raise Exception("Could not bypass Incapsulata")

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        name = soup.find("span", {"data-ui-id": "page-title-wrapper"}).text.strip()
        sku = (
            soup.find("div", "product attribute sku").find("div", "value").text.strip()
        )
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"].strip()
        )
        stock = -1

        picture_urls = magento_picture_urls(soup)

        description = "{}\n\n{}".format(
            html_to_markdown(str(soup.find("div", "additional-attributes-wrapper"))),
            html_to_markdown(str(soup.find("div", "description"))),
        )

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
            cls.currency_iso,
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
