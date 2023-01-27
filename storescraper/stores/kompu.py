from decimal import Decimal
import logging
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup
from storescraper.categories import *
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, remove_words, \
    session_with_proxy


class Kompu(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            ALL_IN_ONE,
            TABLET,
            NOTEBOOK,
            PRINTER,
            MONITOR,
            TELEVISION,
            KEYBOARD_MOUSE_COMBO,
            POWER_SUPPLY,
            COMPUTER_CASE,
            RAM,
            MOUSE,
            HEADPHONES,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            KEYBOARD,
            CASE_FAN,
            UPS,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['almacenamiento/discos-de-estados-solido', SOLID_STATE_DRIVE],
            ['almacenamiento/discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
            ['almacenamiento/discos-duros-internos', STORAGE_DRIVE],
            ['almacenamiento/memorias-flash', MEMORY_CARD],
            ['almacenamiento/pendrive-almacenamiento', USB_FLASH_DRIVE],
            ['apple/imac', ALL_IN_ONE],
            ['apple/ipad', TABLET],
            ['apple/mac', NOTEBOOK],
            ['computadores/notebooks', NOTEBOOK],
            ['computadores/tablet', TABLET],
            ['computadores/todo-en-uno', ALL_IN_ONE],
            ['impresoras-y-plotter/escaneres', PRINTER],
            ['impresoras-y-plotter/inkjet', PRINTER],
            ['impresoras-y-plotter/laser', PRINTER],
            ['impresoras-y-plotter/laser-multifuncional', PRINTER],
            ['impresoras-y-plotter/matriz-de-púnto', PRINTER],
            ['impresoras-y-plotter/plotter', PRINTER],
            ['monitores-y-proyectores/monitores', MONITOR],
            ['monitores-y-proyectores/televisores', TELEVISION],
            ['partes-y-piezas/combos-teclados-y-mouses', KEYBOARD_MOUSE_COMBO],
            ['partes-y-piezas/fuentes-de-poder', POWER_SUPPLY],
            ['partes-y-piezas/gabinetes', COMPUTER_CASE],
            ['partes-y-piezas/memorias-ram-genericos', RAM],
            ['partes-y-piezas/memorias-ram-propietarios', RAM],
            ['partes-y-piezas/mouse', MOUSE],
            ['partes-y-piezas/perifericos', HEADPHONES],
            ['partes-y-piezas/placas-madres', MOTHERBOARD],
            ['partes-y-piezas/procesadores', PROCESSOR],
            ['partes-y-piezas/tarjetas-graficas', VIDEO_CARD],
            ['partes-y-piezas/teclados', KEYBOARD],
            ['partes-y-piezas/ventiladores', CASE_FAN],
            ['ups-y-proteccion-electrica/ups', UPS],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.kompu.cl/categoria-producto/{}/?p' \
                    'age={}'.format(url_extension, page)
                print(url_webpage)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('div', 'card')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if "404 No encontrado" in soup.text:
            return []

        parsed_url = urlparse(url)
        product_id = parse_qs(parsed_url.query)['productID'][0].split('?')[0]
        category_id = parsed_url.path.split('/')[-1]

        product_data_url = 'https://www.kompu.cl/product/{}/quick-view-dialo' \
            'g/{}?fresh=2'.format(product_id, category_id)
        product_response = session.get(product_data_url)

        product_data = product_response.json()['data']['details']

        key = str(product_data['id'])
        name = product_data['name']
        sku = product_data['product_id']
        offer_price = Decimal(product_data['price'])
        stock = product_data['cantidad']
        picture_urls = [i['getProductImageURL']
                        for i in product_data['allImages']]

        part_number_label_tag = soup.find('td', text='Numero de partes')
        if part_number_label_tag:
            part_number = part_number_label_tag.parent.findAll(
                'td')[1].text.strip()
        else:
            part_number = None

        normal_price = Decimal(
            remove_words(soup.find('span', {
                'ng-if': '!productDetailsCtrl.productDiscount.isDiscountExist'}
            ).findAll('span')[-1].text))

        description = html_to_markdown(
            soup.find('div', 'lw-product-details').text) + '&nbsp;'

        product_info = soup.find(
            'div',
            {'ng-class':
                "{ 'dimmer-content' : productDetailsCtrl.pageStatus == false}"}
        )
        product_table = product_info.find('div', 'table-responsive')
        if product_table:
            description += html_to_markdown(product_table.text)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number
        )
        return [p]
