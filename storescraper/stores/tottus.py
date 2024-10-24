from bs4 import BeautifulSoup
import json

from storescraper import banner_sections as bs
from storescraper.utils import session_with_proxy
from .falabella import Falabella


class Tottus(Falabella):
    store_and_subdomain = "tottus"
    seller = [{"id": "TOTTUS", "section_prefix": None, "include_in_fast_mode": True}]
    seller_blacklist = []
    banners_base_url = "https://tottus.cl/"

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super().products_for_url(
            url, category=category, extra_args=extra_args
        )

        for product in products:
            product.url = url
            product.discovery_url = url
            product.seller = None

        return products

    @classmethod
    def banners(cls, extra_args=None):
        session = session_with_proxy(extra_args)
        banners = []
        soup = BeautifulSoup(session.get(cls.banners_base_url).text, "lxml")
        json_data = json.loads(soup.find("script", {"id": "__NEXT_DATA__"}).text)
        props = json_data["props"]["pageProps"]["page"]["containers"]
        banners_data = None

        for container in props:
            if container["key"] == "showcase":
                banners_data = container["components"][0]["data"]["slides"]

        for idx, banner in enumerate(banners_data):
            banners.append(
                {
                    "url": cls.banners_base_url,
                    "picture_url": banner["imgBackgroundDesktopUrl"],
                    "destination_urls": [banner["mainUrl"]],
                    "key": banner["imgBackgroundDesktopUrl"],
                    "position": idx + 1,
                    "section": bs.HOME,
                    "subsection": bs.HOME,
                    "type": bs.SUBSECTION_TYPE_HOME,
                }
            )

        if not banners:
            raise Exception(f"No banners for Home section: {cls.banners_base_url}")

        return banners
