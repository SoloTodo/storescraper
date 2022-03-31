from decimal import Decimal
import json
import logging
import traceback
from bs4 import BeautifulSoup
from storescraper.categories import GAMING_CHAIR, GAMING_DESK, HEADPHONES, \
    KEYBOARD, MONITOR, MOTHERBOARD, MOUSE, NOTEBOOK, POWER_SUPPLY, PROCESSOR, \
    RAM, SOLID_STATE_DRIVE, VIDEO_CARD
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy


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
            ['t-graficas', VIDEO_CARD],
            ['zona-gamer/sillas-gamer', GAMING_CHAIR],
            ['zona-gamer/escritorios-gamer', GAMING_DESK],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.absolutec.cl/categoria-producto/' \
                    '{}/page/{}/'.format(url_extension, page)
                ini_data = session.get(url_webpage).text
                ini_soup = BeautifulSoup(ini_data, 'html.parser')
                data = ini_soup.find('script', {'type': 'text/template'})
                if not data:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                soup = BeautifulSoup(
                    json.loads(data.text),
                    'html.parser')
                product_containers = soup.findAll('div', 'product-inner')
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        ini_data = session.get(url).text
        ini_soup = BeautifulSoup(ini_data, 'html.parser')
        data = ini_soup.find('script', {'type': 'text/template'})
        try:
            soup = BeautifulSoup(json.loads(data.text), 'html.parser')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return []
        json_data = json.loads(ini_soup.findAll(
            'script', {'type': 'application/ld+json'})[1].text)

        key = ini_soup.find('link', {'rel': 'shortlink'})[
            'href'].split('=')[-1]

        name = json_data['name']
        sku = str(json_data['sku'])
        price = Decimal(json_data['offers'][0]['price'])

        add_btn = soup.find('button', 'single_add_to_cart_button')
        if add_btn:
            stock = -1
        else:
            stock = 0

        picture_urls = []
        image_containers = soup.find('div', 'product-images')
        if image_containers:
            images = image_containers.findAll('img', 'img-responsive')
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
