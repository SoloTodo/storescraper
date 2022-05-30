import logging
import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import GAMING_CHAIR, HEADPHONES, MEMORY_CARD, \
    USB_FLASH_DRIVE, ALL_IN_ONE, WEARABLE, CPU_COOLER
from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Winpy(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Tablet',
            'VideoCard',
            'Ram',
            'Cell',
            'StorageDrive',
            'SolidStateDrive',
            'Processor',
            'Motherboard',
            'ComputerCase',
            'PowerSupply',
            CPU_COOLER,
            'Printer',
            'ExternalStorageDrive',
            'Mouse',
            'Television',
            'StereoSystem',
            'Headphones',
            'Ups',
            GAMING_CHAIR,
            MEMORY_CARD,
            USB_FLASH_DRIVE,
            ALL_IN_ONE,
            WEARABLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.winpy.cl'

        category_paths = [
            ['portatiles/notebooks/', 'Notebook'],
            ['portatiles/mobile-workstation/', 'Notebook'],
            ['zona-notebook-gamers/', 'Notebook'],
            ['portatiles/celulares/', 'Cell'],
            ['portatiles/tablet/', 'Tablet'],
            ['memorias/para-notebook/', 'Ram'],
            ['almacenamiento/disco-estado-solido/', 'SolidStateDrive'],
            ['almacenamiento/disco-duro-notebook/', 'StorageDrive'],
            ['computadores/todo-en-uno/', ALL_IN_ONE],
            ['memorias/para-computadores/', 'Ram'],
            ['almacenamiento/disco-duro-pc-s/', 'StorageDrive'],
            ['partes-y-piezas/tarjetas-de-video/', 'VideoCard'],
            ['accesorios/mouse-y-teclados/', 'Mouse'],
            ['partes-y-piezas/placas-madres/', 'Motherboard'],
            ['partes-y-piezas/procesadores/', 'Processor'],
            ['memorias/', 'Ram'],
            ['partes-y-piezas/gabinetes/', 'ComputerCase'],
            ['partes-y-piezas/fuente-de-poder/', 'PowerSupply'],
            ['partes-y-piezas/disipadores/', CPU_COOLER],
            ['zona-mouse-y-teclados-gamer/', 'Mouse'],
            ['zona-audifonos-gamer/', HEADPHONES],
            ['accesorios/sillas-y-mesas/', GAMING_CHAIR],
            ['almacenamiento/nas/', 'StorageDrive'],
            ['almacenamiento/discos-portatiles/', 'ExternalStorageDrive'],
            ['almacenamiento/discos-sobremesa/', 'ExternalStorageDrive'],
            ['almacenamiento/memorias-flash/', MEMORY_CARD],
            ['almacenamiento/pendrive/', USB_FLASH_DRIVE],
            ['apple/imac/', ALL_IN_ONE],
            ['apple/macbook-pro-retina/', 'Notebook'],
            ['apple/ipad/', 'Tablet'],
            ['apple/watch/', WEARABLE],
            ['monitores/', 'Monitor'],
            ['impresoras/', 'Printer'],
            ['accesorios/audifonos/', 'Headphones'],
            ['accesorios/parlantes/', 'StereoSystem'],
            ['ups/ups/', 'Ups'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = base_url + '/' + category_path

            page = 1
            while True:
                if page >= 30:
                    raise Exception('Page overflow: ' + category_path)

                url_with_page = url + 'paged/' + str(page) + '/'
                print(url_with_page)
                soup = BeautifulSoup(session.get(url_with_page).text,
                                     'html5lib')
                product_containers = soup.find('section', {'id': 'productos'})
                product_containers = product_containers.findAll('article')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + category_path)
                    break

                for container in product_containers:
                    product_url = 'https://www.winpy.cl' + \
                                  container.find('a')['href']
                    product_urls.append(product_url)

                if not soup.find('div', 'paginador'):
                    break

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.url != url:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html5lib')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        part_number = soup.find('span', 'sku').text.strip()
        sku = part_number

        condition_str = soup.find('span',
                                  {'itemprop': 'itemCondition'}).text.strip()

        condition_dict = {
            'NUEVO': 'https://schema.org/NewCondition',
            'REEMBALADO': 'https://schema.org/RefurbishedCondition',
            'REACONDICIONADO': 'https://schema.org/RefurbishedCondition',
            'SEMI-NUEVO': 'https://schema.org/RefurbishedCondition',
            'USADO': 'https://schema.org/UsedCondition',
            'DE SHOW ROOM': 'https://schema.org/RefurbishedCondition',
            'OUTLET': 'https://schema.org/RefurbishedCondition',
        }

        condition = condition_dict[condition_str]

        if soup.find('div', 'sinstock'):
            stock = 0
            normal_price = Decimal(remove_words(
                soup.find('meta',
                          {'property': 'product:price:amount'})['content']
            ))
            offer_price = normal_price
        else:
            stock = int(soup.find('p', {'itemprop': 'offerCount'}).text)

            offer_price = Decimal(remove_words(soup.find(
                'h2', {'itemprop': 'lowPrice'}).string))

            normal_price = Decimal(remove_words(soup.find(
                'h3', {'itemprop': 'highPrice'}).string))

        description = html_to_markdown(str(soup.find('div', 'info')))

        picture_tags = soup.findAll('img', {'itemprop': 'image'})

        picture_urls = ['https://www.winpy.cl' + urllib.parse.quote(tag['src'])
                        for tag in picture_tags]

        flixmedia_id = None
        video_urls = None
        flixmedia_tag = soup.find(
            'script', {'src': '//media.flixfacts.com/js/loader.js'})

        if flixmedia_tag:
            try:
                flixmedia_id = flixmedia_tag['data-flix-mpn']
                video_urls = flixmedia_video_urls(flixmedia_id)
            except KeyError:
                pass

        p = Product(
            name,
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
            part_number=part_number,
            condition=condition,
            description=description,
            picture_urls=picture_urls,
            flixmedia_id=flixmedia_id,
            video_urls=video_urls
        )

        return [p]
