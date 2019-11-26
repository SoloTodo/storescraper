from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Olier(Store):
    base_url = 'https://www.lg.com'
    country_code = 'cl'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'Stove',
            'WashingMachine',
            'AirConditioner'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['tv-c148', 'Television'],
            ['reproductores-portatiles-c140', 'StereoSystem'],
            ['equipo-de-sonido-c138', 'StereoSystem'],
            ['celulares-c142', 'Cell'],
            ['heladeras-c42', 'Refrigerator'],
            ['freezer-c40', 'Refrigerator'],
            ['horno-electrico-c16', 'Oven'],
            ['microondas-c20', 'Oven'],
            ['encimeras-c13', 'Stove'],
            ['cocinas-c12', 'Stove'],
            ['lavarropas-c18', 'WashingMachine'],
            ['secarropas-c22', 'WashingMachine'],
            ['aire-split-c28', 'AirConditioner'],
        ]

        session = session_with_proxy(extra_args)
