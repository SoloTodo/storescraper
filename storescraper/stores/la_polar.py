from bs4 import BeautifulSoup

from .abcdin import AbcDin
from storescraper import banner_sections as bs
from storescraper.utils import session_with_proxy


class LaPolar(AbcDin):
    base_url = "https://www.lapolar.cl"
    site_name = "LaPolar"

    @classmethod
    def banners(cls, extra_args=None):
        session = session_with_proxy(extra_args)
        banners = []

        soup = BeautifulSoup(session.get(cls.base_url).text, "lxml")
        slider_tags = soup.findAll("div", "rojoPolar")

        for index, slider_tag in enumerate(slider_tags):
            destination_urls = [slider_tag.find("a")["href"]]
            picture_url = slider_tag.find("source")["srcset"]

            banners.append(
                {
                    "url": cls.base_url,
                    "picture_url": picture_url,
                    "destination_urls": destination_urls,
                    "key": picture_url,
                    "position": index + 1,
                    "section": bs.HOME,
                    "subsection": bs.HOME,
                    "type": bs.SUBSECTION_TYPE_HOME,
                }
            )

        if not banners:
            raise Exception("No banners for Home section: " + cls.base_url)

        return banners
