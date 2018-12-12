from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class CasaRoyal(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Mouse',
            'Headphones',
            'Keyboard',
            'KeyboardMouseCombo',
            'Printer',
            'PowerSupply',
            'SolidStateDrive',
            'StorageDrive',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'VideoGameConsole',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['comunicaciones/celulares/', 'Cell'],
            ['computacion/accesorios-computacion/mouse-gamer/', 'Mouse'],
            ['computacion/accesorios-computacion/mouse-inalambricos/',
             'Mouse'],
            ['computacion/accesorios-computacion/mouse-inalambricos/',
             'Mouse'],
            ['categoria-producto/computacion/accesorios-computacion/'
             'mouse-usb/', 'Mouse'],
            ['categoria-producto/computacion/accesorios-computacion/'
             'audifonos-gamer/', 'Headphones'],
            ['computacion/accesorios-computacion/audifono-gamer/',
             'Headphones'],
            ['computacion/accesorios-computacion/teclados-inalambricos/',
             'Keyboard'],
            ['computacion/accesorios-computacion/teclados-numericos/',
             'Keyboard'],
            ['computacion/accesorios-computacion/teclados-usb/', 'Keyboard'],
            ['computacion/accesorios-computacion/teclado-gamer/', 'Keyboard'],
            ['computacion/accesorios-computacion/teclado-gaming/', 'Keyboard'],
            ['computacion/equipos-impresion/impresoras/', 'Printer'],
            ['computacion/equipos-impresion/impresora-multifuncional/',
             'Printer'],
            ['computacion/componentes-pc/fuente-poder-atx/', 'PowerSupply'],
            ['computacion/componentes-pc/discos-ssd/', 'SolidStateDrive'],
            ['computacion/componentes-pc/discos-ssd/', 'SolidStateDrive'],
            ['computacion/almacenamiento/', 'MemoryCard'],
            ['computacion/consolas-y-juegos/consolas-de-videojuegos/',
             'VideoGameConsole'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + category_path)

                url_webpage = 'https://www.casaroyal.cl/categoria-producto/' \
                              '{}?pag={}'.format(category_path, page)
                print(url_webpage)
                soup = BeautifulSoup(session.get(url_webpage).text,
                                     'html.parser')

                link_containers = soup.findAll('article', 'producto')

                if not link_containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                for link_container in link_containers:
                    product_url = link_container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        sku_tags = soup.findAll('span', 'sku')

        if len(sku_tags) < 2:
            return []

        base_name = soup.find('h1', 'title-producto').text.strip()
        model = sku_tags[0].text.split(':')[1].strip()
        name = '{} ({})'.format(base_name, model)
        sku = sku_tags[1].text.split(':')[1].strip()
        stock = -1

        price_text = soup.find('div', 'prod-info').find(
            'span', 'precio-right').text
        price = Decimal(remove_words(price_text))
        description = html_to_markdown(str(soup.find('div', 'bgLightGrey')))
        picture_urls = []

        for container in soup.find('div', 'galleria').findAll('a'):
            try:
                picture_urls.append(container['data-zoom-image'])
            except KeyError:
                pass

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
