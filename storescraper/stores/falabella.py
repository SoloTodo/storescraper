import json
import urllib
from collections import OrderedDict
from decimal import Decimal
import requests

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words


class Falabella(Store):
    @classmethod
    def product_types(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'HomeTheater',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Projector',
            'VideoGameConsole',
            'CellAccesory',
            'AllInOne',
            'AirConditioner',
            'Monitor',
            'WaterHeater',
            'SolidStateDrive',
            'Mouse',
            'SpaceHeater',
        ]

    @classmethod
    def products_for_url(cls, url, product_type=None, extra_args=None):
        session = requests.Session()
        session.headers.update({
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en,en-US;q=0.8,es;q=0.6',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'DNT': '1',
            'Host': 'www.falabella.com',
            'Referer': 'http://www.falabella.com/falabella-cl/',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 '
                          'Safari/537.36'
        })
        session.get('http://www.falabella.com/falabella-cl/')
        session.get('http://www.falabella.com/falabella-cl/'
                    'includes/ajaxFirstNameAndCartQuantity.jsp')

        url_schema = url.replace(
            'http://www.falabella.com/falabella-cl/category/', '')

        query_args = OrderedDict([
            ('currentPage', 1),
            ('sortBy', '2'),
            ('navState', "/category/{}?sortBy=2".format(url_schema))])

        page = 1
        products = []

        while True:
            res = None

            error_count = 0
            while res is None or 'errors' in res:
                error_count += 1
                if error_count > 10:
                    raise Exception('Error threshold exceeded')
                query_args['currentPage'] = page
                pag_url = 'http://www.falabella.com/rest/model/' \
                          'falabella/rest/browse/BrowseActor/' \
                          'get-product-record-list?{}'.format(
                            urllib.parse.quote(json.dumps(
                                query_args, separators=(',', ':')), safe=''))

                res = json.loads(session.get(pag_url).content.decode('utf-8'))

            for product_entry in res['state']['resultList']:
                product_id = product_entry['productId']
                product_url = \
                    'http://www.falabella.com/falabella-cl/product/{}/' \
                    ''.format(product_id)
                product_name = product_entry['title']
                sku = product_entry['skuId']
                description = product_entry['title']
                picture_url = 'http://falabella.scene7.com/is/image/' \
                              'Falabella/{}'.format(sku)

                prices = {e['type']: e for e in product_entry['prices']}

                lookup_field = 'originalPrice'
                if lookup_field not in prices[3]:
                    lookup_field = 'formattedLowestPrice'

                normal_price = Decimal(remove_words(prices[3][lookup_field]))

                if 1 in prices:
                    lookup_field = 'originalPrice'
                    if lookup_field not in prices[1]:
                        lookup_field = 'formattedLowestPrice'
                    offer_price = Decimal(
                        remove_words(prices[1][lookup_field]))
                else:
                    offer_price = normal_price

                product_prices = {
                    pmtype: normal_price
                    for pmtype in ['cash', 'debit_card', 'credit_card']
                }

                product_prices['cmr_card'] = offer_price

                p = Product(
                    product_name,
                    cls.__name__,
                    product_type,
                    product_url,
                    url,
                    sku,
                    -1,
                    normal_price,
                    offer_price,
                    'CLP',
                    part_number=None,
                    sku=sku,
                    description=description,
                    cell_plan_name=None,
                    cell_monthly_payment=None,
                    picture_url=picture_url
                )

                products.append(p)

            if res['state']['pagesTotal'] == page:
                break

            page += 1

        return products

    @classmethod
    def discover_urls_for_product_type(cls, product_type, extra_args=None):
        url_schemas = [
            ['cat5860031/Notebooks-Convencionales', 'Notebook'],
            ['cat2028/Notebooks-Gamers', 'Notebook'],
            ['cat2450060/Notebooks-2-en-1', 'Notebook'],
            ['cat5860030/MacBooks', 'Notebook'],
            ['cat70043/Televisores', 'Television'],
            ['cat3118/Tablet', 'Tablet'],
            ['cat4074/No-Frost', 'Refrigerator'],
            ['cat4091/Side-by-Side', 'Refrigerator'],
            ['cat4036/Frio-Directo', 'Refrigerator'],
            ['cat4048/Freezer', 'Refrigerator'],
            ['cat4049/Frigobar', 'Refrigerator'],
            ['cat1840004/Cavas-de-Vino', 'Refrigerator'],
            ['cat2049/Impresoras', 'Printer'],
            ['cat3151/Microondas', 'Oven'],
            ['cat3114/Hornos-Electricos', 'Oven'],
            ['cat3025/Aspiradoras-y-Enceradoras', 'VacuumCleaner'],
            ['cat4060/Lavadoras', 'WashingMachine'],
            ['cat1700002/Lavadora-Secadora', 'WashingMachine'],
            ['cat4088/Secadoras', 'WashingMachine'],
            ['cat1280018/Celulares-Basicos', 'Cell'],
            ['cat720161/Smartphones', 'Cell'],
            ['cat70028/Camaras-Compactas', 'Camera'],
            ['cat70029/Camaras-Semiprofesionales', 'Camera'],
            ['cat3091/Equipos-de-Musica', 'StereoSystem'],
            ['cat3171/Parlantes-y-Docking', 'StereoSystem'],
            ['cat2032/DVD-y-Blu-Ray', 'OpticalDiskPlayer'],
            ['cat2045/Home-Theater', 'HomeTheater'],
            ['cat3087/Discos-duros', 'ExternalStorageDrive'],
            ['cat3177/Pendrives', 'UsbFlashDrive'],
            ['cat70037/Tarjetas-de-Memoria', 'MemoryCard'],
            ['cat2070/Proyectores', 'Projector'],
            ['cat3770004/Consolas', 'VideoGameConsole'],
            ['cat40051/All-In-One', 'AllInOne'],
            ['cat7830015/Portatiles', 'AirConditioner'],
            ['cat2062/Monitores', 'Monitor'],
            ['cat2013/Calefont-y-Termos', 'WaterHeater'],
            ['cat3155/Mouse', 'Mouse'],
            ['cat3097/Estufas', 'SpaceHeater'],
        ]

        urls = []

        for url_schema, ptype in url_schemas:
            if ptype != product_type:
                continue

            urls.append('http://www.falabella.com/falabella-cl/category/{}'
                        ''.format(url_schema))

        return urls
