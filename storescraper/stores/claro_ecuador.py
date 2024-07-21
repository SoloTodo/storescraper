import json
import shlex
from decimal import Decimal

import subprocess
from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION, CELL, NOTEBOOK, PRINTER, WEARABLE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions


class ClaroEcuador(StoreWithUrlExtensions):
    url_extensions = [
        ("tecnologia/api/general/catalogo", TELEVISION),
        ("tv/api/general/catalogo", TELEVISION),
        ("laptops/api/general/catalogo", NOTEBOOK),
        ("postpago/api/general/catalogo", CELL),
        ("iot/api/general/catalogo", CELL),
        ("ofertas/api/tu-vida-conectada---impresora/catalogo", PRINTER),
        ("ofertas/api/tu-vida-conectada---wearables/catalogo", WEARABLE),
    ]

    @classmethod
    def curl_post_request(cls, url):
        command = (
            "curl --location '"
            + url
            + "' \
--header 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
--header 'X-Requested-With: XMLHttpRequest' \
--data 'financiamiento%5Btipo_pago%5D=contado&financiamiento%5Bcuotas%5D=18&financiamiento%5Briesgo%5D=&financiamiento%5Bentrada%5D=0&financiamiento%5Btarifa%5D=0'"
        )
        # Define the command to execute using curl
        print(command)
        command = shlex.split(command)

        # Execute the curl command and capture the output
        result = subprocess.run(command, capture_output=True, text=True)

        # Return the stdout of the curl command
        return result.stdout

    @classmethod
    def curl_get_request(cls, url):
        command = "curl --location '" + url + "'"
        # Define the command to execute using curl
        print(command)
        command = shlex.split(command)

        # Execute the curl command and capture the output
        result = subprocess.run(command, capture_output=True, text=True)

        # Return the stdout of the curl command
        return result.stdout

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        product_urls = []
        url_webpage = "https://catalogo.claro.com.ec/{}".format(url_extension)
        print(url_webpage)
        output = cls.curl_post_request(url_webpage)
        products_json = json.loads(output)
        path = url_extension.split("/")[0]
        if path == "ofertas":
            path = "tecnologia"

        for slug, product in products_json["content"]["productos"].items():
            if product["marca"] != "LG":
                continue

            product_url = "https://catalogo.claro.com.ec/{}/ver-mas/{}".format(
                path, slug
            )
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        response = cls.curl_get_request(url)
        soup = BeautifulSoup(response, "lxml")
        color_selectors = soup.findAll("input", {"name": "color"})
        key = color_selectors[0]["value"]
        assert len(color_selectors) == 1

        name = soup.find("h1").text.strip()
        picture_tags = soup.find("div", "productoGaleriaShow").findAll("img")
        # The page repeats the pictures, no idea why
        picture_tags = picture_tags[: (len(picture_tags) // 2)]
        picture_urls = [
            "https://catalogo.claro.com.ec/" + tag["data-src"] for tag in picture_tags
        ]

        slug = url.split("/")[-1]
        endpoint = "https://catalogo.claro.com.ec/api/general/productos/{}/detalles/precios".format(
            slug
        )
        response = cls.curl_post_request(endpoint)
        prices_json = json.loads(response)
        best_price = Decimal(0)
        for price_entry in prices_json["content"]["preciosNormales"]:
            calculated_price = Decimal(
                price_entry["cuotas"] * price_entry["cuotaPrConImp"]
            )
            if not calculated_price:
                continue
            if not best_price or calculated_price < best_price:
                best_price = calculated_price
        best_price = best_price.quantize(Decimal("0.01"))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            -1,
            best_price,
            best_price,
            "USD",
            sku=key,
            picture_urls=picture_urls,
        )

        return [p]
