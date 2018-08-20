from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13, \
    html_to_markdown


class SearsMexico(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['4610/accesorios', 'MemoryCard'],
            ['4605/software-y-accesorios', 'UsbFlashDrive'],
            ['15131/almacenamiento', 'UsbFlashDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'https://www.sears.com.mx/categoria/{}/?ver=todos' \
                           ''.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            containers = soup.findAll('div', 'caja_producto')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_link = container.find('a', 'producto_nombre')

                name = product_link.text.lower()

                if 'gb' not in name and 'tb' not in name:
                    continue

                product_url = 'https://www.sears.com.mx/producto/' + \
                              product_link['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        pricing_tag = soup.find(
            'script', {'src': 'https://media.flixfacts.com/js/loader.js'})

        sku = pricing_tag['data-flix-sku']

        ean = pricing_tag['data-flix-sku']
        if len(ean) == 12:
            ean = '0' + ean
        if not check_ean13(ean):
            ean = None

        name = soup.find('h1').text.strip()

        price = soup.find('div', 'precio').text.split('$')[1].replace(',', '')
        price = Decimal(price)

        description = html_to_markdown(
            str(soup.find('div', 'descripcion_larga')))

        picture_urls = [tag.find('a')['href'] for tag in
                        soup.findAll('div', 'fotito')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'MXN',
            sku=sku,
            ean=ean,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
