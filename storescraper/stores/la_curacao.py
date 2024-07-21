from decimal import Decimal
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import (
    html_to_markdown,
    session_with_proxy,
    magento_picture_urls,
)


class LaCuracao(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1
        done = False

        while not done:
            if page > 50:
                raise Exception("Page overflow")

            url_webpage = (
                "https://www.lacuracao.pe/curacao/marca-lg.html" "?brand=LG&p={}"
            ).format(page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, "lxml")
            product_containers = soup.findAll("li", "product")

            if not product_containers:
                break

            for container in product_containers:
                product_url = container.find("a")["href"]
                if product_url in product_urls:
                    done = True
                    break
                product_urls.append(product_url)

            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        name = soup.find("span", {"itemprop": "name"}).text.strip()
        sku = soup.find("div", {"itemprop": "sku"}).text.strip()
        if soup.find("button", {"id": "product-addtocart-button"}):
            stock = -1
        else:
            stock = 0
        price = Decimal(
            soup.find("meta", {"property": "product:price:amount"})["content"]
        )

        picture_urls = magento_picture_urls(soup)

        description = html_to_markdown(
            str(soup.find("div", "product-view-bottom-content"))
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
            "PEN",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
