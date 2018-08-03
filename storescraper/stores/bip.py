from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Bip(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'VideoCard',
            'Processor',
            'Monitor',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'CpuCooler',
            'Tablet',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Television',
            'Mouse',
            'Printer',
            'Camera',
            'AllInOne',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Notebooks
            ['166', 'Notebook'],
            # Cámaras digitales
            ['2', 'Camera'],
            # All in One
            ['218', 'AllInOne'],
            # Tarjetas de video
            ['118', 'VideoCard'],
            # Proces
            ['784', 'Processor'],
            # Monitores
            ['761', 'Monitor'],
            # Placas madre
            ['785', 'Motherboard'],
            # RAM PC
            ['132', 'Ram'],
            # RAM Notebook
            ['178', 'Ram'],
            # Disco Duro 2,5'
            ['125', 'StorageDrive'],
            # Disco Duro 3,5'
            ['124', 'StorageDrive'],
            # Disco Duro SSD
            ['413', 'SolidStateDrive'],
            # Fuentes de poder
            ['88', 'PowerSupply'],
            # Gabinetes
            ['8', 'ComputerCase'],
            # Gabinetes gamer
            ['707', 'ComputerCase'],
            # Coolers CPU
            ['5', 'CpuCooler'],
            # Tablets
            ['286', 'Tablet'],
            # Discos externos 2.5
            ['128', 'ExternalStorageDrive'],
            # USB Flash
            ['528', 'UsbFlashDrive'],
            # Memory card
            ['82', 'MemoryCard'],
            # Mouse
            ['20', 'Mouse'],
            # Mouse Gamer
            ['703', 'Mouse'],
            # Impresoras
            ['769', 'Printer'],
            # Plotter
            ['770', 'Printer'],
            # Teclados
            ['12', 'Keyboard'],
            # Audífono/Micrófono
            ['70', 'Headphones'],
            # Parlantes
            ['13', 'StereoSystem'],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            offset = 0

            while True:
                if offset >= 200:
                    raise Exception('Page overflow: ' + url_extension)

                url_webpage = 'https://www.bip.cl/categoria/{}/{}'.format(
                    url_extension, offset
                )

                print(url_webpage)

                data = session.get(url_webpage).text

                soup = BeautifulSoup(data, 'html5lib')
                product_containers = soup.findAll('div', 'producto')

                if not product_containers:
                    if offset == 0:
                        raise Exception('Empty category: ' + url_webpage)
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                offset += 20

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html5lib')

        name = soup.find('h2', 'title-product').text.strip()
        sku = soup.find('span', 'text-stock').text.strip()

        if soup.find('span', 'text-to-bg'):
            stock = -1
        else:
            stock = 0

        price_containers = soup.findAll('p', 'precio')

        offer_price = Decimal(remove_words(price_containers[0].text.strip()))
        normal_price = Decimal(remove_words(price_containers[2].text.strip()))

        if normal_price < offer_price:
            normal_price = offer_price

        description = html_to_markdown(
                str(soup.find('div', {'id': 'description'})))

        picture_urls = [tag['src'] for tag in
                        soup.findAll('img', 'primary-img')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
