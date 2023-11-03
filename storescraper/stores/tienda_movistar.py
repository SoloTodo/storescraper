from storescraper.categories import HEADPHONES, TABLET, CELL, WEARABLE, \
    VIDEO_GAME_CONSOLE, STEREO_SYSTEM, TELEVISION, NOTEBOOK
from .movistar import Movistar


class TiendaMovistar(Movistar):
    variations = []
    category_paths = [
        ('celulares', CELL),
        ('outlet/celulares-reacondicionados', CELL),
        ('outlet/tablets', TABLET),
        ('outlet/smartwatch', WEARABLE),
        ('outlet/accesorios', HEADPHONES),
        ('smartwatch', WEARABLE),
        ('tablets', TABLET),
        ('audifonos', HEADPHONES),
        ('gaming/consolas', VIDEO_GAME_CONSOLE),
        ('gaming/accesorios-gamer', HEADPHONES),
        ('smarthome', TELEVISION),
        ('accesorios/parlantes-bluetooth', STEREO_SYSTEM),
        ('notebooks', NOTEBOOK),
    ]

    @classmethod
    def categories(cls):
        return [
            CELL,
            TABLET,
            HEADPHONES,
            WEARABLE,
            VIDEO_GAME_CONSOLE,
            STEREO_SYSTEM
        ]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super(TiendaMovistar, cls).products_for_url(url)
        for product in products:
            product.key = product.sku
            product.cell_plan_name = None
            product.cell_monthly_payment = None
            if 'seminuevo' in product.url:
                product.condition = 'https://schema.org/RefurbishedCondition'
        return products
