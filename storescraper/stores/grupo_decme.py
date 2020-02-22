from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, \
    html_to_markdown


class GrupoDecme(Store):
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
            'AllInOne',
            'VideoGameConsole'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['discos-duros-internos', 'StorageDrive'],
            ['tarjetas-madre', 'Motherboard'],
            ['procesadores', 'Processor'],
            ['disipadores-y-ventiladores', 'CpuCooler'],
            ['memorias-ram', 'Ram'],
            ['tarjetas-de-video', 'VideoCard'],
            ['fuentes-de-poder', 'PowerSupply'],
            ['gabinetes', 'ComputerCarse'],
            ['mouse', 'Mouse'],
            ['teclados', 'Keyboard'],
            ['monitores', 'Monitor'],
            ['tablets', 'Tablet'],
            ['laptops-1', 'Notebook'],
            ['impresion', 'Printer'],
            ['celulares', 'Cell'],
            ['televisores-y-smart-tv', 'Television'],
            ['consolas', 'VideoGameConsole']
        ]

        base_url = 'https://grupodecme.com/collections/{}?page={}'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)

                if page >= 15:
                    raise Exception('Page overflow' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                products = soup.findAll('a', 'product-grid-item')

                if not products:
                    if page == 1:
                        raise Exception('Empty url: ' + url)
                    break

                for product in products:
                    product_url = 'https://grupodecme.com{}'.format(
                        product['href'])
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text
        sku = soup.find('span', 'variant-sku').text

        stock_container = soup.find\
            ('span', {'id': 'variantQuantity-product-template__message'})

        if not stock_container:
            stock = 0
        else:
            stock_text = stock_container.text
            stock = int(stock_text.split()[2])

        price = soup.find('span', {'id': 'productPrice-product-template'})\
            .find('span', 'visually-hidden').text

        price = Decimal(price.replace('$', '').replace(',', ''))

        images = soup.findAll('meta', {'property': 'og:image:secure_url'})
        picture_urls = [i["content"] for i in images]

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

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
            'MXN',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
