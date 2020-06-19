import re

from collections import defaultdict
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class MercadoTech(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Tablet',
            'Notebook',
            'StereoSystem',
            'OpticalDiskPlayer',
            'PowerSupply',
            'ComputerCase',
            'Motherboard',
            'Processor',
            'VideoCard',
            'CpuCooler',
            'Printer',
            'Ram',
            'Monitor',
            'MemoryCard',
            'Mouse',
            'Cell',
            'UsbFlashDrive',
            'Television',
            'Camera',
            'Projector',
            'AllInOne',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'VideoGameConsole',
            'Ups',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):

        category_urls = [
            ['tecnologia/partes-y-piezas/almacenamiento/discos-duros', 'StorageDrive']
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                page_url = 'https://www.mercadotech.cl/t/{}?page={}'\
                    .format(category_path, page)

                soup = BeautifulSoup(session.get(page_url).text, 'html.parser')

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        pass
