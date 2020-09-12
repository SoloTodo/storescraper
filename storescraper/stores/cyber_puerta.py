import logging

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import STORAGE_DRIVE, SOLID_STATE_DRIVE, \
    MOTHERBOARD, PROCESSOR, CPU_COOLER, RAM, VIDEO_CARD, POWER_SUPPLY, \
    COMPUTER_CASE, MOUSE, KEYBOARD, KEYBOARD_MOUSE_COMBO, MONITOR, TABLET, \
    NOTEBOOK, CELL, TELEVISION, VIDEO_GAME_CONSOLE, EXTERNAL_STORAGE_DRIVE


class CyberPuerta(Store):
    @classmethod
    def categories(cls):
        return [
            STORAGE_DRIVE,
            SOLID_STATE_DRIVE,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            RAM,
            VIDEO_CARD,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOUSE,
            KEYBOARD,
            KEYBOARD_MOUSE_COMBO,
            MONITOR, TABLET,
            NOTEBOOK,
            CELL,
            TELEVISION,
            VIDEO_GAME_CONSOLE,
            EXTERNAL_STORAGE_DRIVE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['Computo-Hardware/Discos-Duros-SSD-NAS/Discos-Duros-Externos',
             EXTERNAL_STORAGE_DRIVE],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/'
             'Discos-Duros-Internos-para-PC', STORAGE_DRIVE],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/Discos-Duros-para-NAS',
             STORAGE_DRIVE],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/'
             'Discos-Duros-Internos-para-Laptop', STORAGE_DRIVE],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/'
             'Discos-Duros-para-Videovigilancia', STORAGE_DRIVE],
            ['Computo-Hardware/Discos-Duros-SSD-NAS/SSD',
             SOLID_STATE_DRIVE],
            ['Computo-Hardware/Componentes/Tarjetas-Madre', MOTHERBOARD],
            ['Computo-Hardware/Componentes/Procesadores/Procesadores-para-PC',
             PROCESSOR],
            ['Computo-Hardware/Componentes/Enfriamiento-Ventilacion/'
             'Disipadores-para-CPU', CPU_COOLER],
            ['Computo-Hardware/Componentes/Enfriamiento-Ventilacion/'
             'Refrigeracion-Liquida', CPU_COOLER],
            ['Computo-Hardware/Memorias-RAM-Flash/Memorias-RAM-para-PC',
             RAM],
            ['Computo-Hardware/Memorias-RAM-Flash/Memorias-RAM-para-Laptop',
             RAM],
            ['Computo-Hardware/Memorias-RAM-Flash/Memorias-RAM-para-Mac',
             RAM],
            ['Computo-Hardware/Componentes/Tarjetas-de-Video', VIDEO_CARD],
            ['Computo-Hardware/Componentes/Fuentes-de-Poder-para-PC-s',
             POWER_SUPPLY],
            ['Computo-Hardware/Componentes/Gabinetes', COMPUTER_CASE],
            ['Computo-Hardware/Dispositivos-de-entrada/Mouse', MOUSE],
            ['Computo-Hardware/Dispositivos-de-entrada/Teclados', KEYBOARD],
            ['Computo-Hardware/Dispositivos-de-entrada/'
             'Kits-de-Teclado-y-Mouse', KEYBOARD_MOUSE_COMBO],
            ['Computo-Hardware/Monitores/Monitores', MONITOR],
            ['Computadoras/Tabletas/Tabletas', TABLET],
            ['Computadoras/Laptops', NOTEBOOK],
            # ['Impresion-Copiado/Impresoras-Multifuncionales/Impresoras',
            #  PRINTER],
            # ['Impresion-Copiado/Impresoras-Multifuncionales/'
            #  'Impresoras-Fotograficas', PRINTER],
            # ['Impresion-Copiado/Impresoras-Multifuncionales/Multifuncionales',
            #  PRINTER],
            ['Telecomunicacion/Telefonia-Movil/Smartphones', CELL],
            ['Audio-Video/TV-Pantallas/Pantallas-LED/', TELEVISION],
            # ['Computadoras/All-in-One', ALL_IN_ONE],
            ['Audio-Video/Consolas-Juegos/Nintendo-Switch/'
             'Consolas-Nintendo-Switch', VIDEO_GAME_CONSOLE],
            ['Audio-Video/Consolas-Juegos/Xbox-One/Consolas-Xbox-One',
             VIDEO_GAME_CONSOLE],
            ['Audio-Video/Consolas-Juegos/Nintendo', VIDEO_GAME_CONSOLE],
            ['Audio-Video/Consolas-Juegos/Playstation-4-PS4/'
             'Consolas-Playstation-4', VIDEO_GAME_CONSOLE],
            ['Audio-Video/Consolas-Juegos/Nintendo-2DS/Consolas-Nintendo-2DS',
             VIDEO_GAME_CONSOLE]
        ]

        base_url = 'https://www.cyberpuerta.mx/{}/'
        filter = 'Filtro/Estatus/En-existencia/EnviadoDesde/MEX'

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension)
                if page > 1:
                    url = url + str(page) + '/'
                url = url + filter

                if page >= 100:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_container = soup.find('ul', {'id': 'productList'})\

                if not product_container:
                    if page == 1:
                        logging.warning('Empty category: ' + url)
                    break

                products = product_container.findAll('li', 'productData')

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'detailsInfo_right_title').text
        sku = soup.find('div', 'detailsInfo_right_artnum')\
            .text.replace('SKU:', '').strip()

        if not soup.find('span', 'stockFlag'):
            stock = 0
        else:
            stock = int(soup.find('span', 'stockFlag').find('span').text)

        if not soup.find('span', 'priceText'):
            return []

        price = Decimal(soup.find('span', 'priceText')
                        .text.replace('$', '').replace(',', ''))

        if soup.find('div', 'detailsInfo_left_picture_morepictures')\
                .find('div', 'emslider2_items'):
            picture_urls = []
            images = soup.find('div', 'detailsInfo_left_picture_morepictures')\
                .find('div', 'emslider2_items').findAll('li')

            for image in images:
                picture_urls.append(image.find('a')['data-src'])
        else:
            picture_urls = None

        description = html_to_markdown(
            str(soup.find('div', 'cpattributes-box')))

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
            part_number=sku
        )

        return [p]
