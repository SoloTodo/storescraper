from decimal import Decimal
import demjson
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, CELL, EXTERNAL_STORAGE_DRIVE, \
    HEADPHONES, MONITOR, NOTEBOOK, POWER_SUPPLY, PRINTER, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, STEREO_SYSTEM, TABLET, TELEVISION, VIDEO_CARD, \
    VIDEO_GAME_CONSOLE, WEARABLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class AZTech(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            ALL_IN_ONE,
            TABLET,
            SOLID_STATE_DRIVE,
            MONITOR,
            WEARABLE,
            EXTERNAL_STORAGE_DRIVE,
            PROCESSOR,
            RAM,
            VIDEO_CARD,
            POWER_SUPPLY,
            VIDEO_GAME_CONSOLE,
            TELEVISION,
            PRINTER,
            STEREO_SYSTEM,
            CELL
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computacion/notebook', NOTEBOOK],
            ['computacion/escritorio', ALL_IN_ONE],
            ['computacion/tablet', TABLET],
            ['computacion/almacenamiento-datos', SOLID_STATE_DRIVE],
            ['computacion/monitores', MONITOR],
            ['mundo-apple/mac/portatil/macbook-pro', NOTEBOOK],
            ['mundo-apple/mac/portatil/macbook-air', NOTEBOOK],
            ['mundo-apple/mac/escritorio/imac', ALL_IN_ONE],
            ['mundo-apple/ipad/ipad-pro', TABLET],
            ['mundo-apple/ipad/ipad-air', TABLET],
            ['mundo-apple/ipad/ipad-102', TABLET],
            ['mundo-apple/ipad/ipad-mini', TABLET],
            ['apple-watch-ultra', WEARABLE],
            ['apple-watch-series-8', WEARABLE],
            ['mundo-apple/watch/apple-watch-series-7', WEARABLE],
            ['mundo-apple/watch/apple-watch-nike-series-7', WEARABLE],
            ['mundo-apple/watch/apple-watch-se', WEARABLE],
            ['mundo-apple/watch/apple-watch-nike-se', WEARABLE],
            ['mundo-apple/watch/apple-watch-series-3', WEARABLE],
            ['mundo-apple/airpods', HEADPHONES],
            ['mundo-apple/accesorios/almacenamiento', EXTERNAL_STORAGE_DRIVE],
            ['componentes/procesadores', PROCESSOR],
            ['componentes/memorias-ram', RAM],
            ['componentes/almacenamiento', SOLID_STATE_DRIVE],
            ['componentes/tarjetas-de-video', VIDEO_CARD],
            ['componentes/fuente-de-poder', POWER_SUPPLY],
            ['mundo-gamers/consolas', VIDEO_GAME_CONSOLE],
            ['hogar-y-oficina/television', TELEVISION],
            ['hogar-y-oficina/impresoras', PRINTER],
            ['hogar-y-oficina/escaner-y-plotter', PRINTER],
            ['hogar-y-oficina/smartwatches', WEARABLE],
            ['audio-y-video/audio', STEREO_SYSTEM],
            ['celulares/marcas-1', CELL],
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
                url_webpage = 'https://azt.cl/{}?page={}'.format(
                    url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll(
                    'div', 'product-block__wrapper')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append('https://azt.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        json_data = None
        try:
            json_data = demjson.decode(soup.find(
                'script', {'type': 'application/ld+json'}).text)
        except Exception as e:
            pass

        key = soup.find('meta', {'property': 'og:id'})['content']
        description = soup.find('meta', {'name': 'description'})['content']
        if 'instock' in soup.find(
                'meta', {'property': 'product:availability'})['content']:
            stock = -1
        else:
            stock = 0

        picture_urls = []
        picture_container = soup.find('div', 'product-gallery__slider')
        if picture_container:
            for i in picture_container.findAll('img'):
                picture_urls.append(i['src'])
        else:
            picture_urls.append(
                soup.find('img', 'product-gallery__image')['data-src'])

        if json_data:
            for entry in json_data:
                if entry['@type'] == 'Product':
                    product_data = entry
                    break
            else:
                raise Exception('No JSON product data found')

            name = product_data['name']
            sku = product_data['sku']
            price = Decimal(product_data['offers']['price']).quantize(0)
        else:
            name = soup.find('h1', 'product-heading__title').text
            sku = soup.find(
                'span',
                'product-heading__detail--sku').text.replace('SKU: ', '')
            price_discount_tag = soup.find(
                'h2', 'product-heading__pricing--has-discount')
            if price_discount_tag:
                price_text = price_discount_tag.find('span').text
            else:
                price_text = soup.find('h2', 'product-heading__pricing').text
            price = Decimal(remove_words(price_text))

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
            part_number=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
