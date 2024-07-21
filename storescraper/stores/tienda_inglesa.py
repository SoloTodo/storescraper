import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13


class TiendaInglesa(Store):
    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [TELEVISION]
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        products_urls = []
        for local_category in url_extensions:
            if local_category != category:
                continue
            page = 0
            done = False
            while not done:
                if page > 10:
                    raise Exception("page overflow: " + local_category)
                url_webpage = (
                    "https://www.tiendainglesa.com.uy/busqueda?"
                    '0,0,LG,0,0,0,rel,%5B"Lg"%5D,false,%5B%5D,%5B%5D,,{}'.format(page)
                )
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, "lxml")

                i = soup.find("input", {"name": "GXState"})["value"]
                json_data = json.loads(i)

                done = True
                for key in json_data.keys():
                    if key.endswith("PRODUCTUI"):
                        done = False
                        products_url = json_data[key]["Info"]["Uri"]
                        products_urls.append(
                            "https://www.tiendainglesa.com.uy" + products_url
                        )
                page += 1
        return products_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        )
        response = session.get(url)

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, "html5lib")

        i = soup.find("input", {"name": "GXState"})["value"]
        json_data = json.loads(i)["vPRODUCTUI"]

        name = json_data["Info"]["Name"]
        description = json_data["Info"]["ProductObs"]
        sku = json_data["Info"]["ProductCode"]
        raw_ean = json_data["Info"]["ProductBarCode"]
        ean = raw_ean if check_ean13(raw_ean) else None
        price = Decimal(str(json_data["Prices"][0]["Price"]))
        stock = json_data["QuickBuy"]["StockMax"]

        picture_urls = [i["ProductImageUrl"] for i in json_data["Pictures"]]
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
            ean=ean,
            picture_urls=picture_urls,
            description=description,
        )
        return [p]
