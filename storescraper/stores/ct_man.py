import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PRINTER, KEYBOARD, HEADPHONES, \
    GAMING_CHAIR, COMPUTER_CASE, RAM, POWER_SUPPLY, PROCESSOR, MOTHERBOARD, \
    VIDEO_CARD, EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, MONITOR, \
    KEYBOARD_MOUSE_COMBO, NOTEBOOK, SOLID_STATE_DRIVE, ALL_IN_ONE, \
    TELEVISION, CELL, VIDEO_GAME_CONSOLE, MOUSE, CPU_COOLER
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class CtMan(StoreWithUrlExtensions):
    url_extensions = [
        ['notebooks/types/notebooks', NOTEBOOK],
        ['notebooks/types/memorias-ram-para-laptops', RAM],
        ['notebooks/types/memorias-ram', RAM],
        ['notebooks/types/notebook', NOTEBOOK],
        ['pc-escritorio/types/all-in-one', ALL_IN_ONE],
        ['pc-escritorio/types/gabinetes', COMPUTER_CASE],
        ['pc-escritorio/types/memorias-ram', RAM],
        ['perifericos-de-pc/types/impresoras', PRINTER],
        ['perifericos-de-pc/types/kits-de-mouse-y-teclado',
         KEYBOARD_MOUSE_COMBO],
        ['perifericos-de-pc/types/teclados-fisicos', KEYBOARD],
        ['perifericos-de-pc/types/audifonos', HEADPHONES],
        ['perifericos-de-pc/types/mouses', MOUSE],
        ['perifericos-de-pc/types/impresoras-a-color', PRINTER],
        ['repuestos-y-componentes/types/coolers-para-pc', CPU_COOLER],
        ['repuestos-y-componentes/types/fuentes-de-poder', POWER_SUPPLY],
        ['repuestos-y-componentes/types/tarjetas-de-video', VIDEO_CARD],
        ['repuestos-y-componentes/types/procesadores', PROCESSOR],
        ['repuestos-y-componentes/types/placas-madre', MOTHERBOARD],
        ['repuestos-y-componentes/types/memorias-ram', RAM],
        ['repuestos-y-componentes/types/packs', PROCESSOR],
        ['almacenamiento/types/discos-duros-externos', EXTERNAL_STORAGE_DRIVE],
        ['almacenamiento/types/ssds-externos', EXTERNAL_STORAGE_DRIVE],
        ['almacenamiento/types/ssd', SOLID_STATE_DRIVE],
        ['almacenamiento/types/pen-drives', USB_FLASH_DRIVE],
        ['almacenamiento/types/monitores', MONITOR],
        ['monitores/types/monitores', MONITOR],
        ['monitores/types/televisores', TELEVISION],
        ['electronica-audio-y-video/types/audifonos', HEADPHONES],
        ['celulares-y-telefonia/types/celulares-y-smartphones', CELL],
        ['gaming/types/audifonos', HEADPHONES],
        ['gaming/types/fuentes-de-alimentacion', POWER_SUPPLY],
        ['gaming/types/sillas-gamer', GAMING_CHAIR],
        ['gaming/types/gabinetes', COMPUTER_CASE],
        ['gaming/types/ssd', SOLID_STATE_DRIVE],
        ['gaming/types/memorias-ram', RAM],
        ['gaming/types/placas-madre', MOTHERBOARD],
        ['gaming/types/monitores', MONITOR],
        ['gaming/types/notebooks', NOTEBOOK],
        ['gaming/types/procesadores', PROCESSOR],
        ['gaming/types/memorias-ram-para-laptops', RAM],
        ['gaming/types/fuentes-de-poder', POWER_SUPPLY],
        ['gaming/types/tarjetas-de-video', VIDEO_CARD],
        ['gaming/types/kits-de-mouse-y-teclado', KEYBOARD_MOUSE_COMBO],
        ['gaming/types/consolas-de-videojuegos', VIDEO_GAME_CONSOLE],
        ['gaming/types/mouses', MOUSE],
        ['gaming/types/coolers-para-pc', CPU_COOLER],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 25:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://www.ctman.cl/collections/{}/' \
                          '{}'.format(url_extension, page)
            print(url_webpage)
            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('li', 'product-item')
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
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        key_tag = soup.find('div', 'title-description').find(
            'input', {'name': 'cart_item[variant_id]'})

        if not key_tag:
            return []

        key = key_tag['value']
        name = soup.find('h1', 'product-title').text.strip()
        sku = soup.find('p', 'product-sku').text.split(':')[1].strip()
        description = html_to_markdown(
            str(soup.find('div', 'product-description')))
        price_tag = soup.find('div', 'precio-product').find(
            'span', 'bootic-price')
        price = Decimal(remove_words(price_tag.text))
        stock_text = soup.find('p', 'units-in-stock').text.strip()

        if stock_text == 'Producto agotado':
            stock = 0
        else:
            stock = int(stock_text.split(':')[1])

        picture_urls = []
        for i in soup.findAll('li', 'product-asset'):
            parsed_url = urllib.parse.urlparse(i.find('a')['href'])
            picture_url = parsed_url._replace(
                path=urllib.parse.quote(parsed_url.path)
            ).geturl()
            picture_urls.append(picture_url)

        part_number_tag = soup.find('p', 'part-number')
        if part_number_tag:
            part_number = soup.find('p', 'part-number').contents[1].strip()
        else:
            part_number = None

        special_tags = soup.find('div', 'special-tags').findAll(
            'span', 'special-tag')

        condition = 'https://schema.org/NewCondition'

        for special_tag in special_tags:
            if 'special-tag-3' in special_tag.attrs['class']:
                # Sin accesorios
                condition = 'https://schema.org/RefurbishedCondition'
            if 'special-tag-4' in special_tag.attrs['class']:
                condition = 'https://schema.org/DamagedCondition'

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
            part_number=part_number,
            condition=condition
        )
        return [p]
