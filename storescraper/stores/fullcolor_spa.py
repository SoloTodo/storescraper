import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOUSE, HEADPHONES, KEYBOARD, MONITOR, \
    POWER_SUPPLY, COMPUTER_CASE, SOLID_STATE_DRIVE, KEYBOARD_MOUSE_COMBO, \
    PRINTER, STEREO_SYSTEM, MEMORY_CARD, USB_FLASH_DRIVE, STORAGE_DRIVE, \
    GAMING_CHAIR, MICROPHONE
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
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            STORAGE_DRIVE,
            GAMING_CHAIR,
            MICROPHONE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # gamer mouse
            ['subcategoria.asp?/id/4', MOUSE],
            ['subcategoria.asp?/id/76', MOUSE],
            # gamer headphones
            ['subcategoria.asp?/id/99', HEADPHONES],
            ['subcategoria.asp?/id/101', HEADPHONES],
            # gamer keyboard
            ['subcategoria.asp?/id/7', KEYBOARD],
            ['subcategoria.asp?/id/80', KEYBOARD],
            ['segmento.asp?/id/191', MONITOR],
            ['segmento.asp?/id/193', POWER_SUPPLY],
            ['segmento.asp?/id/239', COMPUTER_CASE],
            ['segmento.asp?/id/243', SOLID_STATE_DRIVE],
            ['segmento.asp?/id/244', SOLID_STATE_DRIVE],
            ['segmento.asp?/id/82', KEYBOARD_MOUSE_COMBO],
            ['segmento.asp?/id/175', KEYBOARD_MOUSE_COMBO],
            ['subcategoria.asp?/id/83', PRINTER],
            ['subcategoria.asp?/id/92', STEREO_SYSTEM],
            ['subcategoria.asp?/id/30', MEMORY_CARD],
            ['segmento.asp?/id/241', STORAGE_DRIVE],
            ['subcategoria.asp?/id/31', USB_FLASH_DRIVE],
            ['subcategoria.asp?/id/88', GAMING_CHAIR],
            ['subcategoria.asp?/id/93', MICROPHONE]
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
        name = soup.find('div', 'product-name').text.strip()
        sku = soup.find('input', {'id': 'id'})['value']
        stock = int(soup.find('span', 'in-stock').text.replace('(', '')
                    .replace(')', '').split()[-1])
        price = Decimal(
            remove_words(soup.find('span', 'price').text.strip().split()[1]))

        picture_container = soup.find('div', 'product-image').find('img')

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
