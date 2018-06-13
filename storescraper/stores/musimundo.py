import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Musimundo(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
            'UsbFlashDrive',
            'MemoryCard',
            'ExternalStorageDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # ['1661~electrohogar/1676~heladeras', 'Refrigerator'],
            # ['1661~electrohogar/1673~freezers/1675~vertical',
            # 'Refrigerator'],
            # ['1661~electrohogar/1673~freezers/1674~horizontal',
            #  'Refrigerator'],
            # ['1551~clima/1552~aire-acondicionado/1554~split',
            #  'AirConditioner'],
            # ['1661~electrohogar/1662~calefones/1664~electrico',
            #  'WaterHeater'],
            # ['1661~electrohogar/1662~calefones/1663~gas',
            #  'WaterHeater'],
            # ['1683~lavarropas/1686~automatico',
            #  'WashingMachine'],
            # ['1683~lavarropas/1685~semiautomatico',
            #  'WashingMachine'],
            # ['1683~lavarropas/1684~manual',
            #  'WashingMachine'],
            # ['1661~electrohogar/1665~hornoscocinas/1666~cocinas',
            #  'Stove'],
            # ['1661~electrohogar/1665~hornoscocinas/1666~cocinas',
            #  'Stove'],
            # ['1661~electrohogar/1665~hornoscocinas/1669~anafe-a-gas',
            #  'Stove'],
            # ['1661~electrohogar/1665~hornoscocinas/'
            #  '1670~anafe-electrico-estandar', 'Stove'],
            # ['1661~electrohogar/1665~hornoscocinas/'
            #  '1671~anafe-electrico-vitroceramico', 'Stove'],
            # ['1661~electrohogar/1665~hornoscocinas/'
            #  '1672~hornos-para-empotrar', 'Stove'],
            ['1625~computacion/1647~accesorios-de-informatica/1656~pen-drive',
             'UsbFlashDrive'],
            ['1625~computacion/1647~accesorios-de-informatica/'
             '1652~memorias-extraibles', 'MemoryCard'],
            ['1625~computacion/1647~accesorios-de-informatica/'
             '1655~disco-portatil', 'ExternalStorageDrive'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.musimundo.com/catalogo/{}/Listado?' \
                           'limitRows=1000'.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            containers = soup.findAll('article', 'product')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                category_url = container.find('a')['href']
                product_urls.append(category_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        sku = re.search(r"'internalId': '(\d+)'", page_source).groups()[0]

        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', 'name').text.strip()
        price_string = soup.find('div', 'online').find('span', 'value').text

        price = Decimal(price_string.replace('.', '').replace(
            '$', '').replace(',', '.'))

        panel_ids = ['divDescription', 'divCardData']

        description = ''

        for panel_id in panel_ids:
            panel = soup.find('div', {'id': panel_id})
            if panel:
                description += html_to_markdown(str(panel)) + '\n\n'

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', 'cloud-zoom-gallery')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
