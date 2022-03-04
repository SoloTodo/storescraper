from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import HEADPHONES, KEYBOARD_MOUSE_COMBO, \
    COMPUTER_CASE, MOUSE, VIDEO_CARD, KEYBOARD, SOLID_STATE_DRIVE, \
    POWER_SUPPLY, NOTEBOOK, RAM, MOTHERBOARD, PROCESSOR, CPU_COOLER, MICROPHONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class NextPc(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            KEYBOARD_MOUSE_COMBO,
            COMPUTER_CASE,
            MOUSE,
            VIDEO_CARD,
            KEYBOARD,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            NOTEBOOK,
            RAM,
            MOTHERBOARD,
            PROCESSOR,
            CPU_COOLER,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['perifericos/headset', HEADPHONES],
            ['combos', KEYBOARD_MOUSE_COMBO],
            ['gabinetes', COMPUTER_CASE],
            ['perifericos/mouse', MOUSE],
            ['hardware/tarjetas-de-video', VIDEO_CARD],
            ['hardware/placa-madre', MOTHERBOARD],
            ['perifericos/teclado', KEYBOARD],
            ['hardware/almacenamiento', SOLID_STATE_DRIVE],
            ['hardware/fuentes-de-poder', POWER_SUPPLY],
            ['notebooks', NOTEBOOK],
            ['hardware/ram', RAM],
            ['hardware/procesadores', PROCESSOR],
            ['hardware/refrigeracion', CPU_COOLER],
            ['perifericos/microfonos', MICROPHONE]
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
                url_webpage = 'https://nextpc.cl/product-category/{}/page' \
                              '/{}/'.format(url_extension, page)
                print(url_webpage)
                res = session.get(url_webpage)

                if res.status_code == 404:
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                product_containers = soup.findAll('div', 'product-grid-item')

                if not product_containers:
                    raise Exception('Page without products: ' + url_webpage)

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
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[1]
        if soup.find('p', 'stock in-stock'):
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        else:
            stock = 0
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(
                remove_words(soup.find('p', 'price').text.split()[0]))
        picture_urls = [tag['src'] for tag in soup.find('div', 'woocommerce'
                                                               '-product'
                                                               '-gallery')
                        .findAll('img')]
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
            picture_urls=picture_urls,

        )
        return [p]
