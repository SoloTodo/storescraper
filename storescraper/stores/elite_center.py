from storescraper.store import Store
from storescraper.categories import HEADPHONES, SOLID_STATE_DRIVE, \
    MOUSE, KEYBOARD, CPU_COOLER, COMPUTER_CASE, \
    POWER_SUPPLY, RAM, MONITOR, MOTHERBOARD, \
    PROCESSOR, VIDEO_CARD, STEREO_SYSTEM, STORAGE_DRIVE
from storescraper.utils import session_with_proxy


class EliteCenter(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            STEREO_SYSTEM,
            STORAGE_DRIVE,
            MOUSE,
            KEYBOARD,
            SOLID_STATE_DRIVE,
            CPU_COOLER,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Stereo System
            ['accesorios-gamer', STEREO_SYSTEM],
            # Storage Drive
            ['almacenamiento', STORAGE_DRIVE],
            # Headphones
            ['audifonos-2', HEADPHONES],
            # Storage Drive
            ['disco-duro-pcs', STORAGE_DRIVE],
            # Solid State Drive
            ['disco-estado-solido', SOLID_STATE_DRIVE],
            # CPU Cooler
            ['disipadores', CPU_COOLER],
            # Power Supply
            ['fuente-de-poder', POWER_SUPPLY],
            # Computer Case
            ['gabinetes', COMPUTER_CASE],
            # Ram
            ['memorias-ram', RAM],
            # Monitor
            ['monitores', MONITOR],
            # Mouse
            ['mouse-2', MOUSE],
            # Mother Board
            ['placas-madres', MOTHERBOARD],
            # Processor
            ['procesadores', PROCESSOR],
            # Video Card
            ['tarjeta-de-video', VIDEO_CARD],
            # Video Card
            ['tarjetas-de-video', VIDEO_CARD],
            # Keyboard
            ['teclados-2', KEYBOARD],

        ]

        session = session_with_proxy(extra_args)
        products_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            offset = 1
            while True:
                if offset > 10:
                    raise Exception('page overflow: ' + url_extensions)

                url_webpage = 'https://elitecenter.cl/product-category/{}/' \
                              '?orderby=popularity&paged={}'.format(url_extension, offset)
