import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Dimercom(Store):
    @classmethod
    def categories(cls):
        return [
            # 'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            'CpuCooler',
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            # 'Ups',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Monitor',
            # 'Headphones',
            'Tablet',
            'Notebook',
            # 'StereoSystem',
            # 'OpticalDiskPlayer',
            'Printer',
            # 'MemoryCard',
            'Cell',
            # 'UsbFlashDrive',
            'Television',
            # 'Camera',
            # 'Projector',
            'AllInOne',
            'VideoGameConsole'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [

        ]

        base_url = '{}{}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        return []
