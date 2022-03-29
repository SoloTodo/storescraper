from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import GAMING_CHAIR, GAMING_DESK, HEADPHONES, \
    KEYBOARD, MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, POWER_SUPPLY, PROCESSOR, \
    RAM, SOLID_STATE_DRIVE, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import HeadlessChrome, html_to_markdown


class Absolutec(Store):
    @classmethod
    def categories(cls):
        return [
            SOLID_STATE_DRIVE,
            POWER_SUPPLY,
            RAM,
            MONITOR,
            MOTHERBOARD,
            PROCESSOR,
            HEADPHONES,
            MOUSE,
            NOTEBOOK,
            KEYBOARD,
            VIDEO_CARD,
            GAMING_CHAIR,
            GAMING_DESK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.absolutec.cl'

        url_extensions = [
            ['discos-duros', SOLID_STATE_DRIVE],
            ['fuentes-de-poder', POWER_SUPPLY],
            ['memoria-ram', RAM],
            ['monitores', MONITOR],
            ['placa-madre', MOTHERBOARD],
            ['procesadores', PROCESSOR],
            ['productos-gamer/audifonos-gamer', HEADPHONES],
            ['productos-gamer/mouse-gamer', MOUSE],
            ['productos-gamer/notebook', NOTEBOOK],
            ['productos-gamer/teclado-gamer', KEYBOARD],
            # ['t-graficas', VIDEO_CARD],
            ['zona-gamer/sillas-gamer', GAMING_CHAIR],
            ['zona-gamer/escritorios-gamer', GAMING_DESK],
        ]

        product_urls = []
        with HeadlessChrome() as driver:
            driver.get(base_url)
            for url_extension, local_category in url_extensions:
                if local_category != category:
                    continue
                page = 1
                while True:
                    if page > 10:
                        raise Exception('Page overflow: ' + url_extension)
                    url_webpage = '{}/categoria-producto/{}/' \
                        'page/{}/'.format(base_url, url_extension, page)
                    driver.get(url_webpage)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    product_containers = soup.findAll('div', 'product-inner')
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
        with HeadlessChrome() as driver:
            driver.get('https://www.exito.com/')
            driver.get(url)

            soup = BeautifulSoup(driver.page_source, 'html5lib')
            json_data = json.loads(soup.findAll(
                'script', {'type': 'application/ld+json'})[1].text)

            key = soup.find('link', {'rel': 'shortlink'})[
                'href'].split('=')[-1]

            name = json_data['name']
            sku = str(json_data['sku'])
            price = Decimal(json_data['offers'][0]['price'])

            stock_span = soup.find('span', 'product-stock out-of-stock')
            if stock_span:
                stock = 0
            else:
                stock = -1

            picture_urls = []
            images = soup.find(
                'div', 'product-images').findAll('img', 'img-responsive')
            for i in images:
                picture_urls.append(i['src'])

            description = html_to_markdown(
                str(soup.find('div', {'id': 'tab-description'})))

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
                description=description
            )
            return [p]
