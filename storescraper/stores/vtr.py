from urllib.parse import urlparse

from decimal import Decimal

from storescraper.categories import CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Vtr(Store):
    prepago_url = "https://vtr.com/productos/moviles/prepago"
    planes_url = "https://www.vtr.com/moviles/MovilesPlanes-planes-multimedia"

    @classmethod
    def categories(cls):
        return ["CellPlan", "Cell"]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []

        if category == "CellPlan":
            product_urls.extend([cls.prepago_url, cls.planes_url])
        elif category == "Cell":
            session = session_with_proxy(extra_args)
            session.headers["user-agent"] = (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
            res = session.get(
                "https://vtr.com/nuevo/page-data/productos/equipos/portabilidad/page-data.json"
            )
            # import ipdb
            #
            # ipdb.set_trace()
            product_entries = res.json()["result"]["data"]["contentfulLandingPage"][
                "products"
            ][0]["products"]

            for product_cell in product_entries:
                product_url = "https://vtr.com/productos/equipos/{}".format(
                    product_cell["contentfulid"]
                )
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
                "VTR Prepago",
                cls.__name__,
                category,
                url,
                url,
                "VTR Prepago",
                -1,
                Decimal(0),
                Decimal(0),
                "CLP",
                allow_zero_prices=True,
            )
            products.append(p)
        elif url == cls.planes_url:
            # Plan Postpago
            products.extend(cls._plans(url, extra_args))
        elif "product" in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception("Invalid URL: " + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        res = session.get(
            "https://vtr.com/nuevo/page-data/productos/moviles/planes-moviles/individuales/page-data.json"
        )
        json_data = res.json()["result"]["data"]["contentfulLandingPage"]["products"][
            0
        ]["products"]

        cuotas_suffixes = [
            " Portabilidad (con cuota de arriendo)",
            " Portabilidad (sin cuota de arriendo)",
            "",
        ]
        products = []

        for plan_entry in json_data:
            base_plan_name = "{} {}".format(
                plan_entry["displayName"].strip(), plan_entry["gigabyte"].strip()
            )
            price = Decimal(plan_entry["salePrice"])

            for suffix in cuotas_suffixes:
                name = base_plan_name + suffix

                p = Product(
                    name,
                    cls.__name__,
                    "CellPlan",
                    url,
                    url,
                    name,
                    -1,
                    price,
                    price,
                    "CLP",
                )

                products.append(p)

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers["user-agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

        parsed_url = urlparse(url)
        product_data = session.get(
            "https://vtr.com/nuevo/page-data{}/page-data.json".format(parsed_url.path)
        ).json()["result"]["data"]["contentfulDeviceV2"]

        base_name = product_data["displayName"]
        products = []

        plan_variations = [
            {
                "suffix": "",
                "main_field": "lineaNueva",
                "secondary_field": "cardPayment",
                "price_field": "totalPrice",
                "cell_monthly_payment_field": None,
            },
            {
                "suffix": " Portabilidad",
                "main_field": "portabilidad",
                "secondary_field": "cardPayment",
                "price_field": "totalPrice",
                "cell_monthly_payment_field": None,
            },
            {
                "suffix": " Portabilidad Cuotas",
                "main_field": "portabilidad",
                "secondary_field": "invoicePayment",
                "price_field": "initialPayment",
                "cell_monthly_payment_field": "quotePrice",
            },
        ]

        for variant in product_data["childSkus"]:
            stock = -1 if variant["active"] else 0
            name = "{} ({})".format(base_name, variant["color"])
            picture_urls = ["https:" + x["file"]["url"] for x in variant["images"]]

            for plan_variant in plan_variations:
                variation_value = product_data["jsonDevicePrices"][
                    plan_variant["main_field"]
                ][plan_variant["secondary_field"]]
                if not variation_value["available"]:
                    continue

                for plan in variation_value["items"]:
                    cell_plan_name = plan["planName"] + plan_variant["suffix"]
                    price = Decimal(plan[plan_variant["price_field"]])
                    if plan_variant["cell_monthly_payment_field"]:
                        cell_monthly_payment = Decimal(
                            plan[plan_variant["cell_monthly_payment_field"]]
                        )
                    else:
                        cell_monthly_payment = Decimal(0)

                    products.append(
                        Product(
                            name,
                            cls.__name__,
                            CELL,
                            url,
                            url,
                            "{} - {}".format(name, cell_plan_name),
                            stock,
                            price,
                            price,
                            "CLP",
                            cell_plan_name=cell_plan_name,
                            cell_monthly_payment=cell_monthly_payment,
                            picture_urls=picture_urls,
                            allow_zero_prices=True,
                        )
                    )
        return products
