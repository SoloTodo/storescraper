from storescraper.categories import GAMING_CHAIR, HEADPHONES, MOUSE
from storescraper.store import Store


class Sevenwin(Store):
    @classmethod
    def categories(cls):
        return [
            GAMING_CHAIR,
            HEADPHONES,
            MOUSE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['seven-win-sillas-gamers', GAMING_CHAIR],
            ['seven-win-audifonos-gamer', HEADPHONES],
            ['seven-win-mouse-gamer', MOUSE]
        ]
