import urllib
from decimal import Decimal
from bs4 import BeautifulSoup
from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, session_with_proxy


class CrediVargas(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        product_urls = []

        url_webpage = "https://credivargas.pe/buscar.php?buscar=LG"
        print(url_webpage)
        data = session.get(url_webpage, timeout=60).text
        soup = BeautifulSoup(data, "lxml")
        product_containers = soup.findAll("li", "product-item")
        if not product_containers:
            # logging.warning('Empty category')
            raise Exception("Empyy site")
        for container in product_containers:
            product_url = container.find("a", "text-blue")["href"]
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=60)
        soup = BeautifulSoup(response.text, "lxml")

        key = url.split("-")[-1]
        name_tag = soup.find("h2", "text-lh-1dot2")

        if not name_tag:
            return []

        name = name_tag.text.strip()

        stock = int(soup.find("span", "text-green").text.replace(" en stock", ""))

        product_info = soup.find("div", "col-wd-9gdot5").find("div", "mb-lg-0")
        price_div = product_info.find("ins", "text-decoration-none")

        if not price_div or "AGOTADO" in price_div.text:
            return []

        sku = product_info.findAll("p")[-1].text.split(":")[-1].strip()

        price = Decimal(remove_words(price_div.text, ["S/.", ","]))
        description = html_to_markdown(product_info.find("h2").text)

        picture_urls = []
        picture_container = soup.find("div", {"id": "sliderSyncingNav"})
        for i in picture_container.findAll("img"):
            parsed_url = urllib.parse.urlparse(i["src"])
            picture_url = parsed_url._replace(
                path=urllib.parse.quote(parsed_url.path)
            ).geturl()
            picture_urls.append(picture_url)

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
            "PEN",
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
