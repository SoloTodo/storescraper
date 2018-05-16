import re
import urllib

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

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
            'CpuCooler',
            'Printer',
            'ExternalStorageDrive',
            'Mouse'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.winpy.cl'

        category_paths = [
            ['portatiles/notebooks/', 'Notebook'],
            # ['portatiles/ultrabook/', 'Notebook'],
            ['portatiles/mobile-workstation/', 'Notebook'],
            ['zona-notebook-gamers/', 'Notebook'],
            # ['apple/macbook-air/', 'Notebook'],
            # ['apple/macbook/', 'Notebook'],
            # ['apple/macbook-pro/', 'Notebook'],
            ['apple/macbook-pro-retina/', 'Notebook'],
            ['portatiles/tablet/', 'Tablet'],
            ['apple/ipad/', 'Tablet'],
            ['monitores/', 'Monitor'],
            ['partes-y-piezas/tarjetas-de-video/',
             'VideoCard'],
            ['memorias/', 'Ram'],
            ['portatiles/celulares/', 'Cell'],
            ['almacenamiento/disco-estado-solido/', 'SolidStateDrive'],
            ['almacenamiento/disco-duro-notebook/', 'StorageDrive'],
            ['almacenamiento/disco-duro-pc-s/', 'StorageDrive'],
            ['partes-y-piezas/procesadores/', 'Processor'],
            ['partes-y-piezas/placas-madres/', 'Motherboard'],
            ['partes-y-piezas/gabinetes/', 'ComputerCase'],
            ['partes-y-piezas/fuente-de-poder/', 'PowerSupply'],
            ['partes-y-piezas/disipadores/', 'CpuCooler'],
            ['impresoras/', 'Printer'],
            ['almacenamiento/discos-portatiles/', 'ExternalStorageDrive'],
            ['accesorios/mouse-y-teclados/', 'Mouse'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url = base_url + '/' + category_path

            page = 1
            local_product_urls = []
            while True:
                if page >= 20:
                    raise Exception('Page overflow: ' + category_path)

                url_with_page = url + 'paged/' + str(page) + '/'
                soup = BeautifulSoup(session.get(url_with_page).text,
                                     'html.parser')
                product_containers = soup.find('section', {'id': 'productos'})
                product_containers = product_containers.findAll('article')

                if not product_containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                break_flag = False
                for container in product_containers:
                    product_url = 'https://www.winpy.cl' + \
                                  container.find('a')['href']
                    if product_url in local_product_urls:
                        break_flag = True
                        break
                    local_product_urls.append(product_url)

                if break_flag:
                    break

                page += 1
            product_urls.extend(local_product_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.url == 'https://www.winpy.cl/no-encontrada':
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')

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
        }

        condition = condition_dict[condition_str]

        if soup.find('div', 'sinstock'):
            stock = 0
            pricing_str = re.search(r'dataLayer = ([\S\s]+?);',
                                    page_source).groups()[0]
            pricing_json = demjson.decode(pricing_str.replace('\xa0', ''))
            normal_price = Decimal(remove_words(
                pricing_json[0]['ecommerce']['detail']['products'][0]['price'])
            )
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

        print(picture_urls)

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
            picture_urls=picture_urls
        )

        return [p]
