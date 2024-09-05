from bs4 import BeautifulSoup

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
        slider_container = soup.find("div", "slideshow-container-desk")
        slider_tags = slider_container.findAll("a")

        for index, slider_tag in enumerate(slider_tags):
            destination_urls = [slider_tag["href"]]
            picture_url = slider_tag.find("img")["src"]

            banners.append(
                {
                    "url": cls.banners_base_url,
                    "picture_url": picture_url,
                    "destination_urls": destination_urls,
                    "key": picture_url,
                    "position": index + 1,
                    "section": bs.HOME,
                    "subsection": bs.HOME,
                    "type": bs.SUBSECTION_TYPE_HOME,
                }
            )
        return banners
