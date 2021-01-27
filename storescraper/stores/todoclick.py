from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import ALL_IN_ONE, NOTEBOOK, STORAGE_DRIVE, \
    POWER_SUPPLY, COMPUTER_CASE, MOTHERBOARD, PROCESSOR, VIDEO_CARD, RAM, \
    TABLET, HEADPHONES, MOUSE, KEYBOARD, MONITOR, PRINTER, USB_FLASH_DRIVE, \
    STEREO_SYSTEM, WEARABLE, GAMING_CHAIR
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, \
    remove_words


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
            GAMING_CHAIR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['notebooks', NOTEBOOK],
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
            ['monitores', MONITOR],
            ['impresoras-laser-impresoras', PRINTER],
            ['impresoras-ink-jet-impresoras', PRINTER],
            ['multifuncional-laser', PRINTER],
            ['multifuncional-ink-jet', PRINTER],
            ['pendrive', USB_FLASH_DRIVE],
            ['parlantes', STEREO_SYSTEM],
            ['soundbar', STEREO_SYSTEM],
            ['smartwatch', WEARABLE],
            ['gamer/sillas-gaming', GAMING_CHAIR]
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
                products = soup.findAll('article', 'product')

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
        name = soup.find('h1', 'product_title').text
        sku = soup.find('span', 'sku_wrapper').text.split()[-1]
        stock = 0
        stock_container = soup.find('p', 'stock in-stock')
        if stock_container:
            stock = int(stock_container.text.split(' ')[0])
        price = Decimal(remove_words(
            soup.find('span', 'woocommerce-Price-amount amount').text))
        images = soup.findAll('img', 'wp-post-image')
        picture_urls = [i['src'] for i in images]
        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))
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
            part_number=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]
