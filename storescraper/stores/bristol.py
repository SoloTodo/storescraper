from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Bristol(Store):
    base_url = 'https://www.lg.com'
    country_code = 'cl'

    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Projector',
            'Cell',
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'VacuumCleaner',
            'Monitor',
            'CellAccesory',
            'Notebook',
            'OpticalDrive',
            'B2B',
            'Headphones',
            'Stove',
            'AirConditioner'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['televisores-hd-c166', 'Television'],
            ['televisores-fhd-c167', 'Television'],
            ['televisores-uhd-4k-c168', 'Television'],
            ['audio-c48', 'StereoSystem'],
            ['proyectores-c169', 'Projector']
        ]
