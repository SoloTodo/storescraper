from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Danaus(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Tablet',
            'Printer',
            'StereoSystem',
            'StorageDrive',
            # 'ExternalStorageDrive'
            # 'UsbFlashDrive',
            # 'MemoryCard',
            # 'SolidStateDrive',
            'Projector',
            'Monitor',
            'AllInOne',
            'Mouse',
            # 'Keyboard',
            'Headphones',
            'Processor',
            'PowerSupply',
            'Ram',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['tecnologia/pc-y-portatiles/notebook', 'Notebook'],
            ['tecnologia/pc-y-portatiles/tablets', 'Tablet'],
            ['tecnologia/impresion/multifuncionales-tinta', 'Printer'],
            ['tecnologia/impresion/impresora-laser', 'Printer'],
            ['tecnologia/audio-video-y-fotografia/parlantes', 'StereoSystem'],
            ['tecnologia/almacenamiento/disco-duros-pc', 'StorageDrive'],
            ['tecnologia/audio-video-y-fotografia/videoproyectores',
             'Projector'],
            ['tecnologia/componentes-partes-y-piezas/monitores', 'Monitor'],
            ['tecnologia/componentes-partes-y-piezas/pantallas', 'Monitor'],
            ['tecnologia/pc-y-portatiles/all-in-one', 'AllInOne'],
            ['tecnologia/componentes-partes-y-piezas/mouse-teclado-y-mousepad',
             'Mouse'],
            ['tecnologia/audio-video-y-fotografia/audifono', 'Headphones'],
            ['tecnologia/componentes-partes-y-piezas/procesadores',
             'Processor'],
            ['tecnologia/componentes-partes-y-piezas/fuentes-poder',
             'PowerSupply'],
            ['tecnologia/componentes-partes-y-piezas/ram', 'Ram'],
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        base_url = 'https://www.danaus.cl/{}.html?p={}'
        product_urls = []

        for url_extension, local_category in category_paths:
            if category != local_category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension, page)
                print(url)

                if page >= 20:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.find('ol', 'products')

                if not product_containers:
                    if page == 1:
                        raise Exception('Empty path:' + url)
                    break

                products = product_containers.findAll('li', 'item')

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code in [410, 404]:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('span', 'sku').text.split(':')[1].strip()
        stock = -1

        offer_price = Decimal(
            soup.find('span', 'special-price').find('span', 'price')
                .text.replace('$', '').replace('.', ''))
        normal_price = Decimal(
            soup.find('span', 'price-credit-card')
                .text.replace('$', '').replace('.', ''))

        picture_urls = [soup.find('div', 'preloaded-image').find('img')['src']]

        description = html_to_markdown(
            str(soup.find('div', 'description')))

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
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
