from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import CASE_FAN, COMPUTER_CASE, GAMING_CHAIR, \
    HEADPHONES, MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, POWER_SUPPLY, PRINTER, \
    PROCESSOR, SOLID_STATE_DRIVE, USB_FLASH_DRIVE, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class PcPart(Store):
    @classmethod
    def categories(cls):
        return [
            HEADPHONES,
            NOTEBOOK,
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            COMPUTER_CASE,
            PRINTER,
            USB_FLASH_DRIVE,
            MONITOR,
            CASE_FAN,
            MOUSE,
            MOTHERBOARD,
            PROCESSOR,
            VIDEO_CARD,
            GAMING_CHAIR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['1', HEADPHONES],
            ['6', MONITOR],
            ['8', CASE_FAN],
            ['9', MOUSE],
            ['10', MOTHERBOARD],
            ['11', PROCESSOR],
            ['12', USB_FLASH_DRIVE],
            ['13', SOLID_STATE_DRIVE],
            ['14', COMPUTER_CASE],
            ['15', POWER_SUPPLY],
            ['16', VIDEO_CARD],
            ['17', NOTEBOOK],
            ['21', GAMING_CHAIR],
            ['27', PRINTER],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://pcpart.cl/php/categories/productos.php'
            data = session.post(url_webpage, data={
                                'categorias': url_extension}).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', 'product-item')
            if not product_containers:
                logging.warning('Empty category: ' + local_category)
            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append('https://pcpart.cl/' + product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = url.split('id=')[-1]

        details_items = soup.find('div', 'details-items')
        name = details_items.find('h2').text

        offer_price = Decimal(remove_words(details_items.find(
            'h3', 'price-detail').text.split('Efectivo')[0]))
        normal_price = Decimal(remove_words(details_items.find(
            'h4', 'subprice-detail').text.split('Otros')[0]))
        model = details_items.find('li', 'd-block').contents[2].strip()
        stock = int(details_items.find('h3', 'hurry-title').find('span').text)

        picture_urls = []
        picture_container = details_items.find(
            'div', {'id': 'imagenes-galeria'})
        for i in picture_container.findAll('img'):
            picture_urls.append(i['src'])

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
            sku=key,
            part_number=model,
            picture_urls=picture_urls,
        )
        return [p]
