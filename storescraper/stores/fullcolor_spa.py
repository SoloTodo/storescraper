from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import *
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class FullcolorSpa(Store):
    @classmethod
    def categories(cls):
        return [
            MOUSE,
            HEADPHONES,
            KEYBOARD,
            MONITOR,
            POWER_SUPPLY,
            COMPUTER_CASE,
            SOLID_STATE_DRIVE,
            KEYBOARD_MOUSE_COMBO,
            PRINTER,
            STEREO_SYSTEM,
            USB_FLASH_DRIVE,
            STORAGE_DRIVE,
            GAMING_CHAIR,
            MICROPHONE,
            MOTHERBOARD,
            GAMING_DESK,
            EXTERNAL_STORAGE_DRIVE,
            CASE_FAN,
            CPU_COOLER,
            PROCESSOR,
            NOTEBOOK,
            TABLET,
            RAM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Gamer
            ['subcategoria.asp?/id/4', MOUSE],
            ['subcategoria.asp?/id/7', KEYBOARD],
            ['subcategoria.asp?/id/28', MICROPHONE],
            ['subcategoria.asp?/id/99', HEADPHONES],
            ['segmento.asp?/id/82', KEYBOARD_MOUSE_COMBO],
            ['segmento.asp?/id/191', MONITOR],
            ['segmento.asp?/id/193', POWER_SUPPLY],
            ['segmento.asp?/id/239', COMPUTER_CASE],
            ['segmento.asp?/id/243', SOLID_STATE_DRIVE],
            ['segmento.asp?/id/270', MOTHERBOARD],
            ['segmento.asp?/id/195', GAMING_CHAIR],
            ['segmento.asp?/id/246', GAMING_DESK],
            # Streaming
            ['subcategoria.asp?/id/93', MICROPHONE],
            ['subcategoria.asp?/id/100', HEADPHONES],
            ['segmento.asp?/id/206', GAMING_CHAIR],
            # Computacion
            ['subcategoria.asp?/id/76', MOUSE],
            ['subcategoria.asp?/id/78', MICROPHONE],
            ['subcategoria.asp?/id/101', HEADPHONES],
            ['subcategoria.asp?/id/92', STEREO_SYSTEM],
            ['subcategoria.asp?/id/80', KEYBOARD],
            ['segmento.asp?/id/185', CASE_FAN],
            ['segmento.asp?/id/244', EXTERNAL_STORAGE_DRIVE],
            ['segmento.asp?/id/287', CPU_COOLER],
            ['segmento.asp?/id/251', MONITOR],
            ['segmento.asp?/id/252', PROCESSOR],
            ['subcategoria.asp?/id/115', NOTEBOOK],
            ['subcategoria.asp?/id/123', TABLET],
            ['subcategoria.asp?/id/83', PRINTER],
            # extra
            ['subcategoria.asp?/id/31', USB_FLASH_DRIVE],
            ['subcategoria.asp?/id/30', RAM],
            ['segmento.asp?/id/175', KEYBOARD_MOUSE_COMBO],
            ['segmento.asp?/id/241', STORAGE_DRIVE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://www.fullcolorspa.com/{}'.format(
                url_extension)
            print(url_webpage)
            data = session.get(url_webpage, timeout=30).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('a', 'product-image')
            if not product_containers:
                break
            for container in product_containers:
                product_url = container['href']
                product_urls.append(
                    'https://www.fullcolorspa.com/' + product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_soup = soup.find('div', 'product-view')

        name = product_soup.find('div', 'product-name').text.strip()
        sku = product_soup.find('input', {'id': 'id'})['value']

        if sku == "":
            return []

        stock = int(product_soup.find('span', 'in-stock').text.replace('(', '')
                    .replace(')', '').split()[-1])
        price = Decimal(
            remove_words(
                product_soup.find('span', 'price').text.strip().split()[1]))

        picture_container = product_soup.find(
            'div', 'product-image').find('img')

        if picture_container:
            picture_urls = ['https://www.fullcolorspa.com' +
                            picture_container['src']]
        else:
            picture_urls = None

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
            picture_urls=picture_urls
        )
        return [p]
