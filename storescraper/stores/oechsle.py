from decimal import Decimal
import logging
from bs4 import BeautifulSoup
from storescraper.categories import AIR_CONDITIONER, ALL_IN_ONE, CELL, \
    HEADPHONES, MONITOR, NOTEBOOK, OVEN, PRINTER, REFRIGERATOR, \
    STEREO_SYSTEM, TELEVISION, WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, html_to_markdown, \
    session_with_proxy


class Oechsle(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            MONITOR,
            STEREO_SYSTEM,
            NOTEBOOK,
            CELL,
            ALL_IN_ONE,
            PRINTER,
            REFRIGERATOR,
            WASHING_MACHINE,
            OVEN,
            AIR_CONDITIONER,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # https://www.oechsle.pe/lg
        #   En esta url se ecuentran todo los productos LG
        #   Existen links a las categorías que contienen productos
        #      LG en el menú lateral
        #   url_extension se encuentra en la petición buscapagina?...
        url_extensions = [
            ['160/171', TELEVISION],
            ['160/168/209', NOTEBOOK],
            ['160/206/1222493', MONITOR],
            ['160/167', STEREO_SYSTEM],
            ['160/1222982', HEADPHONES],
            ['160/170/217', CELL],
            ['160/168/207', ALL_IN_ONE],
            ['160/168/208', PRINTER],
            ['161/332', WASHING_MACHINE],
            ['161/201', REFRIGERATOR],
            ['161/198', OVEN],
            ['161/260/324', AIR_CONDITIONER],
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

                url_webpage = 'https://www.oechsle.pe/buscapagina?fq=C:/{}/&' \
                    'fq=B:599&O=OrderByScoreDESC&PS=36&sl=cc1f325c-7406-439c' \
                    '-b922-9b2e850fcc90&cc=36&sm=0&PageNumber={}&'.format(
                        url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')

                product_containers = soup.findAll('div', 'prod-cont')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_urls.append(container.find('a')['href'])
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        sku_input = soup.find('input', {'id': '___rc-p-id'})
        if not sku_input:
            return []

        sku = sku_input['value']
        product_info = session.get('https://www.oechsle.pe/api/catalog_'
                                   'system/pub/products/search/'
                                   '?fq=productId:' + sku).json()[0]
        name = product_info['productName']
        stock = product_info['items'][0]['sellers'][0]['commertialOffer'][
            'AvailableQuantity']
        normal_price = Decimal(str(
            product_info['items'][0]['sellers'][0]['commertialOffer'][
                'Price']))

        offer_info = session.get('https://api.retailrocket.net/api/1.0/partn'
                                 'er/5e6260df97a5251a10daf30d/items/?itemsId'
                                 's={}&format=json'.format(sku)).json()
        if len(offer_info) != 0 and offer_info[0]['Params']['tarjeta'] != "0":
            offer_price = Decimal(offer_info[0]['Params']['tarjeta'])
        else:
            offer_price = normal_price
        picture_urls = [
            product_info['items'][0]['images'][0]['imageUrl'].split('?')[0]]
        if check_ean13(product_info['items'][0]['ean']):
            ean = product_info['items'][0]['ean']
        else:
            ean = None

        description = product_info.get('description', None)
        if description:
            description = html_to_markdown(description)

        part_number = product_info.get('nomenclatura', None)
        if part_number:
            part_number = part_number[0]

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
            'PEN',
            sku=sku,
            picture_urls=picture_urls,
            ean=ean,
            description=description,
            part_number=part_number,
        )
        return [p]
