import logging
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
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'SolidStateDrive',
            'Projector',
            'Monitor',
            'AllInOne',
            'Mouse',
            'Keyboard',
            'Headphones',
            'Processor',
            'PowerSupply',
            'Ram',
            'Motherboard',
            'VideoCard',
            'ComputerCase',
            'Television',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['computadores-y-tablets/tablets', 'Tablet'],
            ['computadores-y-tablets/notebooks', 'Notebook'],
            ['computadores-y-tablets/workstation/workstation-notebook.html',
             'Notebook'],
            ['computadores-y-tablets/macbooks-imac-ipad', 'Notebook'],
            ['computadores-y-tablets/computadoras-de-escritorio/all-in-one',
             'AllInOne'],
            ['computadores-y-tablets/monitores', 'Monitor'],
            ['computadores-y-tablets/mouse-y-teclado/teclado-gamer',
             'Keyboard'],
            ['computadores-y-tablets/mouse-y-teclado/mouse-gamer', 'Mouse'],
            ['componentes-de-computadores/procesadores',
             'Processor'],
            ['componentes-de-computadores/placas-madres', 'Motherboard'],
            ['componentes-de-computadores/memorias', 'Ram'],
            ['componentes-de-computadores/tarjetas-graficas', 'VideoCard'],
            ['componentes-de-computadores/almacenamiento-interno',
             'StorageDrive'],
            ['componentes-de-computadores/almacenamiento-interno/'
             'disco-duro-interno', 'StorageDrive'],
            ['componentes-de-computadores/almacenamiento-interno/disco-'
             'estado-solido-ssd', 'SolidStateDrive'],
            ['componentes-de-computadores/gabinetes', 'ComputerCase'],
            ['componentes-de-computadores/fuentes-de-poder', 'PowerSupply'],
            ['impresoras-y-tintas/impresoras', 'Printer'],
            ['tv-y-video/tv-y-accesorios', 'Television'],
            ['tv-y-video/sonido', 'StereoSystem'],
            ['audio/audifonos', 'Headphones'],
            ['almacenamiento/discos-duros-externos', 'ExternalStorageDrive'],
            ['almacenamiento/pendrive', 'UsbFlashDrive'],
            ['almacenamiento/tarjetas-de-memoria', 'MemoryCard'],
            ['smart-home/electrodomesticos-inteligentes', 'StereoSystem'],
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
            local_urls = []
            done = False

            while not done:
                url = base_url.format(url_extension, page)
                print(url)

                if page >= 20:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.find('ol', 'products')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty path:' + url)
                    break

                products = product_containers.findAll('li', 'item')

                for product in products:
                    product_url = product.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break
                    local_urls.append(product_url)

                page += 1

            product_urls.extend(local_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, allow_redirects=False)

        if response.status_code in [410, 404, 302]:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('h1', 'page-title').text.strip()
        sku = soup.find('div', 'product-add-form').find(
            'form')['data-product-sku'].strip()
        stock = 0

        if soup.find('button', {'id': 'product-addtocart-button'}):
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
