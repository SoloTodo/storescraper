from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR, CPU_COOLER
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
            CPU_COOLER,
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
            'Ups',
            GAMING_CHAIR
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
            ['792', 'VideoCard'],
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
            ['5', CPU_COOLER],
            ['790', CPU_COOLER],
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
            # UPS
            ['31', 'Ups'],
            # Sillas
            ['591', GAMING_CHAIR],
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

                url_webpage = 'https://bip.cl/categoria/{}/{}'.format(
                    url_extension, offset
                )

                data = session.get(url_webpage, verify=False).text

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
        ajax_session = session_with_proxy(extra_args)
        ajax_session.headers['Content-Type'] = \
            'application/x-www-form-urlencoded; charset=UTF-8'
        response = session.get(url, verify=False)

        if response.status_code in [404, 500]:
            return []

        soup = BeautifulSoup(response.text, 'html5lib')
        name = soup.find('h2', 'title-product').text.strip()
        sku = soup.find('span', 'text-stock').text.strip()
        stocks_container = soup.find('div', 'sucursales-stock')

        if stocks_container and stocks_container.find('i', 'fa-check-circle'):
            stock = -1
        else:
            stock = 0

        price_data = ajax_session.post('https://bip.cl/home/viewProductAjax',
                                       'idProd=' + sku, verify=False).json()
        price = Decimal(price_data['internet_price'].replace('.', ''))

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
            price,
            price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
