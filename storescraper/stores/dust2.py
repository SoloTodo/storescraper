import json
import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import PRINTER, UPS, MOUSE, \
    KEYBOARD, HEADPHONES, STEREO_SYSTEM, GAMING_CHAIR, COMPUTER_CASE, \
    CPU_COOLER, RAM, POWER_SUPPLY, PROCESSOR, MOTHERBOARD, VIDEO_CARD, \
    STORAGE_DRIVE, MEMORY_CARD, EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, \
    MONITOR, KEYBOARD_MOUSE_COMBO, NOTEBOOK, WEARABLE, SOLID_STATE_DRIVE, \
    CASE_FAN
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, \
    remove_words


class Dust2(Store):
    @classmethod
    def categories(cls):
        return [
            PRINTER, UPS, MOUSE, KEYBOARD, HEADPHONES, STEREO_SYSTEM,
            GAMING_CHAIR, COMPUTER_CASE, CPU_COOLER, RAM, POWER_SUPPLY,
            PROCESSOR, MOTHERBOARD, VIDEO_CARD, STORAGE_DRIVE, MEMORY_CARD,
            EXTERNAL_STORAGE_DRIVE, USB_FLASH_DRIVE, MONITOR,
            KEYBOARD_MOUSE_COMBO, NOTEBOOK, WEARABLE, SOLID_STATE_DRIVE,
            CASE_FAN
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['mundo-gamer/mouse-gamer', MOUSE],
            ['mundo-gamer/teclados-gamer', KEYBOARD],
            ['mundo-gamer/kits-gamer', KEYBOARD_MOUSE_COMBO],
            ['mundo-gamer/audifonos-gamer', HEADPHONES],
            ['mundo-gamer/parlantes-gamer', STEREO_SYSTEM],
            ['mundo-gamer/sillas-gamer', GAMING_CHAIR],
            ['mundo-gamer/monitores-gamer', MONITOR],
            ['electronica/notebooks/equipos', NOTEBOOK],
            ['electronica/notebooks/memorias-ram-notebooks', RAM],
            ['electronica/impresoras', PRINTER],
            ['electronica/respaldo-energia', UPS],
            ['electronica/smartband', WEARABLE],
            ['electronica/tarjetas-de-memoria-electronica', MEMORY_CARD],
            ['electronica/pendrives', USB_FLASH_DRIVE],
            ['componentes-de-pc/gabinetes', COMPUTER_CASE],
            ['componentes-de-pc/fans-y-controladores', CASE_FAN],
            ['componentes-de-pc/cooler-para-cpu', CPU_COOLER],
            ['componentes-de-pc/refrigeracion-liquida', CPU_COOLER],
            ['componentes-de-pc/memorias-ram', RAM],
            ['componentes-de-pc/fuentes-de-poder', POWER_SUPPLY],
            ['componentes-de-pc/procesadores', PROCESSOR],
            ['componentes-de-pc/placas-madres', MOTHERBOARD],
            ['componentes-de-pc/tarjetas-de-video', VIDEO_CARD],
            ['componentes-de-pc/almacenamiento/ssd-y-discos-duros',
             STORAGE_DRIVE],
            ['componentes-de-pc/almacenamiento/tarjetas-de-memoria',
             MEMORY_CARD],
            ['componentes-de-pc/almacenamiento/discos-y-ssd-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['componentes-de-pc/almacenamiento/discos-m-2',
             SOLID_STATE_DRIVE],
            ['oficina/teclados-perifericos', KEYBOARD],
            ['oficina/mouse-perifericos', MOUSE],
            ['oficina/combo-teclado-y-mouse', KEYBOARD_MOUSE_COMBO],
            ['oficina/audifonos-audio', HEADPHONES],
            ['oficina/parlantes-audio', STEREO_SYSTEM],
            ['oficina/monitores-oficina', MONITOR],
            ['consolas-y-videojuegos/playstation-5/audifonos-ps5', HEADPHONES],
            ['consolas-y-videojuegos/xbox/audifonos-xbox', HEADPHONES],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 25:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://dust2.gg/categoria-producto/{}/page' \
                              '/{}/?orderby=price'.format(url_extension, page)
                print(url_webpage)
                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')
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
        name = soup.find(
            'div',
            'productDetails__productModel--info-productName'
        ).text.strip()

        preventa = 'PREVENTA' in name

        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'productDetails__productModel--image-moreImages'
        ).findAll('img') if tag['src'] != ""]
        variants = soup.find('form', 'variations_form cart')
        if variants:
            products = []
            json_variants = json.loads(variants['data-product_variations'])
            for variant in json_variants:
                variant_suffix = ''

                if isinstance(variant['attributes'], dict):
                    for key, value in variant['attributes'].items():
                        variant_suffix += '{} {}'.format(key, value)
                else:
                    variant_suffix = 'variante invalida'

                variant_name = name + ' - ' + variant_suffix
                variant_sku = str(variant['variation_id'])
                variant_stock = 0 if variant['max_qty'] == '' or preventa \
                    else variant['max_qty']
                variant_normal_price = Decimal(variant['display_price'])
                variant_offer_price = Decimal(
                    round(variant['display_price'] * 0.93))
                p = Product(
                    variant_name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    variant_sku,
                    variant_stock,
                    variant_normal_price,
                    variant_offer_price,
                    'CLP',
                    sku=variant['sku'],
                    picture_urls=picture_urls,

                )
                products.append(p)

            return products
        else:
            key = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[
                1]
            sku = soup.find(
                'div', 'productDetails__productModel--info-productSKU'
            ).find('h5').text.strip()
            agotado_btn = soup.find('div',
                                    'productModel__info--productAgotado')
            if agotado_btn:
                stock = 0
            else:
                stock_text = soup.find(
                    'div', 'productDetails__productModel--info-productInStock'
                ).find('span').text
                if stock_text == '' or preventa:
                    stock = 0
                else:
                    stock = int(stock_text)
            normal_price = Decimal(remove_words(soup.find(
                'div', 'productDetails__productModel--info-productCardPrice'
            ).find('h3').text))
            offer_price = Decimal(remove_words(
                soup.find(
                    'div',
                    'productDetails__productModel--info-productTransferPrice'
                ).find('h3').text))

            description = html_to_markdown(
                str(soup.find(
                    'div', 'productDetails__productData--specs-info')))

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
                description=description
            )
            return [p]
