from storescraper.store import Store
from storescraper.categories import HEADPHONES, MOUSE, KEYBOARD, \
    KEYBOARD_MOUSE_COMBO, STEREO_SYSTEM, NOTEBOOK, TELEVISION, MONITOR, \
    VIDEO_GAME_CONSOLE


class AllGamersChile(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            STEREO_SYSTEM,
            NOTEBOOK,
            TELEVISION,
            MONITOR,
            VIDEO_GAME_CONSOLE,


        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        pass

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        pass
