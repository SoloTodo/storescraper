from decimal import Decimal
import logging

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, SOLID_STATE_DRIVE, \
    STORAGE_DRIVE, POWER_SUPPLY, COMPUTER_CASE, MOTHERBOARD, PROCESSOR, \
    VIDEO_CARD, RAM, TABLET, HEADPHONES, MOUSE, KEYBOARD, MONITOR, PRINTER, \
    USB_FLASH_DRIVE, STEREO_SYSTEM, VIDEO_GAME_CONSOLE, GAMING_CHAIR, \
    CPU_COOLER, KEYBOARD_MOUSE_COMBO, EXTERNAL_STORAGE_DRIVE, \
    MEMORY_CARD, GAMING_DESK, MICROPHONE
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import html_to_markdown, session_with_proxy


class Todoclick(StoreWithUrlExtensions):
    url_extensions = [
        ['486-all-in-one', ALL_IN_ONE],
        ['483-notebooks', NOTEBOOK],
        ['496-tablets', TABLET],
        ['495-tableta-digitalizadora', TABLET],
        ['491-mouse', MOUSE],
        ['554-teclados', KEYBOARD],
        ['490-combo-teclado-mouse', KEYBOARD_MOUSE_COMBO],
        ['489-audifono', HEADPHONES],
        ['485-parlantes', STEREO_SYSTEM],
        ['493-soundbar', STEREO_SYSTEM],
        ['445-ssd-unidad-de-estado-solido', SOLID_STATE_DRIVE],
        ['443-pendrives', USB_FLASH_DRIVE],
        ['444-tarjetas-de-memoria', MEMORY_CARD],
        ['442-disco-duro-externo', EXTERNAL_STORAGE_DRIVE],
        ['555-hdd-disco-duro-mecanico', STORAGE_DRIVE],
        ['534-teclado-gamer', KEYBOARD],
        ['533-mouse-gamer', MOUSE],
        ['532-kit-gamer', KEYBOARD_MOUSE_COMBO],
        ['571-consolas', VIDEO_GAME_CONSOLE],
        ['513-audifonos-over-ear', HEADPHONES],
        ['552-audifonos-in-ear', HEADPHONES],
        ['video-conferencia-701', HEADPHONES],
        ['514-parlantes-gamer', STEREO_SYSTEM],
        ['524-sillas-gamer', GAMING_CHAIR],
        ['523-escritorios-gamer', GAMING_DESK],
        ['528-microfono', MICROPHONE],
        ['543-monitor', MONITOR],
        ['450-procesadores', PROCESSOR],
        ['448-memoria-ram', RAM],
        ['549-tarjetas-de-video', VIDEO_CARD],
        ['446-fuentes-de-poder', POWER_SUPPLY],
        ['451-refrigeracion', CPU_COOLER],
        ['449-placa-madre', MOTHERBOARD],
        ['535-impresoras', PRINTER],
        ['gabinetes-447', COMPUTER_CASE],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page >= 15:
                raise Exception('Page overflow')

            page_url = 'https://www.todoclick.cl/{}?page=' \
                '{}'.format(url_extension, page)

            print(page_url)
            response = session.get(page_url)

            soup = BeautifulSoup(response.text, 'html.parser')
            products_container = soup.find(
                'div', {'id': 'box-product-grid'})

            if not products_container:
                if page == 1:
                    logging.warning('Empty category: ' + page_url)
                break

            for product in products_container.findAll('div', 'item'):
                product_urls.append(product.find('a')['href'])

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        for r in response.history:
            if r.status_code == 301:
                return []
        soup = BeautifulSoup(response.text, 'html5lib')
        base_name = soup.find('h4', 'name_detail').text
        key = soup.find('input', {'id': 'product_page_product_id'})['value']
        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

        products = []

        sku_tag = soup.find('div', 'reference-detail')
        price_tag = soup.find('span', {'itemprop': 'price'})

        if not sku_tag or not price_tag:
            return []

        sku = sku_tag.text.strip()
        stock = 0
        stock_container = soup.find('div', 'product-quantities')
        if stock_container:
            stock = int(stock_container.find('span')['data-stock'])
        offer_price = Decimal(price_tag['content'])
        normal_price = (offer_price * Decimal('1.05')).quantize(0)
        picture_urls = [tag['data-image-large-src'] for tag in
                        soup.find('ul', 'product-images')
                            .findAll('img')]
        products.append(Product(
            base_name,
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
            part_number=sku,
            picture_urls=picture_urls,
            description=description
        ))

        return products
