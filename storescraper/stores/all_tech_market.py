from decimal import Decimal
from bs4 import BeautifulSoup
import validators

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class AllTechMarket(Store):
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
            url_webpage = (
                "https://www.alltechmarket.ec/productos" "?limit=1000&brand=257"
            )
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, "lxml")
            containers = soup.find("div", {"id": "pdx-products-contaniner-list"})
            for container in containers.findAll("div", "product-card"):
                product = container.find("a")["href"]
                product_urls.append("https://www.alltechmarket.ec" + product)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        product_details = soup.find("div", "product-details")
        name = product_details.find("h1").text
        price_tag = product_details.select_one("#pdx-variant-price")
        if price_tag.find("span"):
            price = Decimal(
                price_tag.find("span").text.strip().replace("$", "").replace(",", "")
            )
        else:
            price = Decimal(price_tag.text.strip().replace("$", "").replace(",", ""))
        sku = product_details.find("span", "text-muted").text.strip()
        stock = 0
        if soup.find("div", "product-badge").text.strip() == "Producto disponible":
            stock = -1

        description = html_to_markdown(
            str(soup.find("div", "row align-items-center py-md-3"))
        )

        picture_container = soup.find("div", "product-gallery-preview")
        picture_urls = []
        for i in picture_container.findAll("img"):
            if validators.url(i["src"]):
                picture_urls.append(i["src"])

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
            description=description,
            picture_urls=picture_urls,
        )
        return [p]
