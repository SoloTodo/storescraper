from decimal import Decimal

import validators
from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.utils import session_with_proxy, remove_words
from storescraper.stores.loi_chile import LoiChile


class LoiUruguay(LoiChile):
    CURRENCY = "USD"
    IMAGE_DOMAIN = "d391ci4kxgasl8"

    @classmethod
    def categories(cls):
        return [TELEVISION]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        res = session.post(
            "https://90i0mrelm2-dsn.algolia.net/1/indexes/*/queries?x-algolia-"
            "agent=Algolia%20for%20JavaScript%20(4.13.0)%3B%20Browser%20(lite)"
            "%3B%20react%20(17.0.2)%3B%20react-instantsearch%20(6.22.0)%3B%20J"
            "S%20Helper%20(3.7.3)&x-algolia-api-key=004b911528dce8b9f9543d1461"
            "c60347&x-algolia-application-id=90I0MRELM2",
            '{"requests":[{"indexName":"uy_products_price_asc","params":"filte'
            'rs=product_enabled%3A1&query=lg"}]}',
        )

        product_urls = []

        for entry in res.json()["results"][0]["hits"]:
            product_urls.append(entry["product_url"])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        name = (
            soup.find("h1", "nombre-producto-info")
            .text.replace("\t", "")
            .replace("\n", "")
        )
        sku = soup.find("span", {"id": "idProducto"}).text

        price_tag = soup.find("div", {"id": "contenedor_precio_detalle_producto"})
        if price_tag:
            price = Decimal(price_tag["data-precio"].replace(",", ".")).quantize(0)
        else:
            price_tag = soup.find("p", "hotsale-precio-hotsale").find("span")
            price = Decimal(remove_words(price_tag.text.replace("USD", "")))

        picture_urls = []

        picture_response = session.get(
            f"https://loi.com.uy/index.php?ctrl=productos&urlseo=smart-tv-lg-4k-43ur7800psb"
        )

        for picture in picture_response.json()["multimedia"]:
            picture_urls.append(
                f"https://{cls.IMAGE_DOMAIN}.cloudfront.net/{picture['url']}"
            )

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            cls.CURRENCY,
            sku=sku,
            picture_urls=picture_urls,
        )
        return [p]
