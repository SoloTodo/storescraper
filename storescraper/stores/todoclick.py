import html
import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, STORAGE_DRIVE, \
    POWER_SUPPLY, COMPUTER_CASE, MOTHERBOARD, PROCESSOR, VIDEO_CARD, RAM, \
    TABLET, HEADPHONES, MOUSE, KEYBOARD, MONITOR, PRINTER, USB_FLASH_DRIVE, \
    STEREO_SYSTEM, WEARABLE, GAMING_CHAIR, CPU_COOLER, KEYBOARD_MOUSE_COMBO, \
    EXTERNAL_STORAGE_DRIVE, MEMORY_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


class Todoclick(Store):
    @classmethod
    def categories(cls):
        return [
            ALL_IN_ONE,
            NOTEBOOK,
            STORAGE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            RAM,
            TABLET,
            HEADPHONES,
            MOUSE,
            KEYBOARD,
            MONITOR,
            PRINTER,
            USB_FLASH_DRIVE,
            STEREO_SYSTEM,
            WEARABLE,
            GAMING_CHAIR,
            CPU_COOLER,
            KEYBOARD_MOUSE_COMBO,
            EXTERNAL_STORAGE_DRIVE,
            STORAGE_DRIVE,
            MEMORY_CARD,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebooks', NOTEBOOK],
            ['notebook-gamer', NOTEBOOK],
            ['all-in-one', ALL_IN_ONE],
            ['disco-duro', STORAGE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['gabinetes', COMPUTER_CASE],
            ['placa-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['tarjetas-de-video', VIDEO_CARD],
            ['memoria-ram', RAM],
            ['tablet', TABLET],
            ['audifonos', HEADPHONES],
            ['audifonos-gamer', HEADPHONES],
            ['mouse-accesorios', MOUSE],
            ['mouse-gamer', MOUSE],
            ['teclados', KEYBOARD],
            ['teclado-gamer', KEYBOARD],
            ['kit-gamer', KEYBOARD_MOUSE_COMBO],
            ['monitores', MONITOR],
            ['monitor-gamer', MONITOR],
            ['impresoras', PRINTER],
            ['pendrive', USB_FLASH_DRIVE],
            ['parlantes', STEREO_SYSTEM],
            ['soundbar', STEREO_SYSTEM],
            ['smartwatch', WEARABLE],
            ['sillas-gaming', GAMING_CHAIR],
            ['ventilador', CPU_COOLER],
            ['externo', EXTERNAL_STORAGE_DRIVE],
            ['disco-duro-interno', STORAGE_DRIVE],
            ['tarjeta-memoria', MEMORY_CARD],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page >= 15:
                    raise Exception('Page overflow')

                if page == 1:
                    page_url = 'https://www.todoclick.cl/categoria/{}/'.format(
                        url_extension)
                else:
                    page_url = 'https://www.todoclick.cl/categoria/{}/page/' \
                               '{}/'.format(url_extension, page)

                print(page_url)
                response = session.get(page_url)

                if response.url != page_url:
                    raise Exception('Mismatch: ' + response.url + ' ' +
                                    page_url)

                soup = BeautifulSoup(response.text, 'html.parser')
                products = soup.findAll('article', 'w-grid-item')

                if not products:
                    break

                for product in products:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html5lib')
        base_name = soup.find('h1', 'w-post-elm').text
        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        products = []
        variants = soup.find('form', 'variations_form')

        if variants:
            container_products = json.loads(
                html.unescape(variants['data-product_variations']))
            is_variant = True
            for product in container_products:
                if not product['attributes']:
                    is_variant = False
                    variant_name = base_name
                else:
                    variant_name = base_name + " - " + next(
                        iter(product['attributes'].values()))
                if product['is_in_stock']:
                    stock = int(product['max_qty'])
                else:
                    stock = 0
                key = str(product['variation_id'])
                sku = str(product['sku'])
                price = Decimal(product['display_price'])
                if product['image']['src'] == '':
                    picture_urls = [tag['src'] for tag in soup.find(
                        'div', 'woocommerce-product-gallery').findAll('img')]
                else:
                    picture_urls = [product['image']['src']]

                p = Product(
                    variant_name,
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
                    part_number=sku,
                    picture_urls=picture_urls,
                    description=description
                )
                if not is_variant:
                    return [p]
                products.append(p)
        else:
            sku = soup.find('span', 'sku').text
            stock = 0
            stock_container = soup.find('p', 'stock in-stock')
            if stock_container:
                stock = int(stock_container.text.split(' ')[0])
            offer_price = Decimal(soup.find(
                'meta', {'property': 'product:price:amount'})['content'])
            assert soup.find('meta', {'property': 'product:price:currency'})[
                       'content'] == 'CLP'
            normal_price = (offer_price * Decimal('1.05')).quantize(0)
            picture_urls = [tag['src'] for tag in soup.find('div',
                            'woocommerce-product-gallery').findAll('img')]
            products.append(Product(
                base_name,
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
                part_number=sku,
                picture_urls=picture_urls,
                description=description
            ))

        return products
