import json
import logging
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import TELEVISION, CAMERA, STEREO_SYSTEM, \
    OPTICAL_DISK_PLAYER, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class SonyStore(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            CAMERA,
            STEREO_SYSTEM,
            OPTICAL_DISK_PLAYER,
            HEADPHONES,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['televisores-y-teatro-en-casa/televisores', TELEVISION],
            ['camaras/cyber-shot', CAMERA],
            ['audio/sistemas-de-audio', STEREO_SYSTEM],
            ['televisores-y-teatro-en-casa/reproductores-de-blu-ray-disc'
             '-y-dvd', OPTICAL_DISK_PLAYER],
            ['televisores-y-teatro-en-casa/teatro-en-casa', STEREO_SYSTEM],
            ['audio/audifonos', HEADPHONES],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://store.sony.cl/{}?PS=48'.format(
                url_extension)

            response = session.get(url_webpage)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('div', 'vtex-search-result'
                                                     '-3-x-galleryItem')

            if not product_containers:
                logging.warning('Empty category: ' + url_extension)

            for container in product_containers:
                product_url = container.find('a')['href']
                product_urls.append('https://store.sony.cl' + product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        json_product = json.loads(
            soup.find('script', {'type': 'application/ld+json'}).text)
        if len(json_product['offers']['offers']) > 1:
            products = []
            api_url = 'https://store.sony.cl/api/catalog_system/pub/products' \
                      '/search?fq=productId:{}'.format(json_product['mpn'])
            api_response = session.get(api_url)
            variations = json.loads(api_response.text)[0]['items']
            for product in variations:
                variation_name = json_product['name'] + ' - ' + \
                                 product['Color'][0]
                part_number = product['name'].replace('|', '').strip()
                sku = product['itemId']
                if product['sellers'][0]['commertialOffer'][
                            'AvailableQuantity'] > 10:
                    stock = 10
                else:
                    stock = product['sellers'][0]['commertialOffer'][
                        'AvailableQuantity']
                price = Decimal(
                    product['sellers'][0]['commertialOffer']['Price'])
                picture_urls = [picture['imageUrl'].split('?v')[0] for picture
                                in product['images']]
                p = Product(
                    variation_name,
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
                    part_number=part_number,
                    picture_urls=picture_urls
                )
                products.append(p)
            return products
        else:

            name = json_product['name'].replace('\xa0', ' ')
            part_number = soup.find('p', 'pasonyb2cqa-shelf'
                                         '-custom-0-x-labelSkuName').text.\
                replace('|', '').strip()
            sku = json_product['sku']
            if soup.find('div', 'pasonyb2cqa-product-custom-0-x-btnSinStock'):
                stock = 0
            else:
                stock = int(soup.find('div', 'pasonyb2cqa-product-custom-0-x-'
                                             'labelStock').text.split()[2])
            price = Decimal(json_product['offers']['offers'][0]['price'])
            picture_urls = [tag['src'].split('-')[0] for tag in
                            soup.findAll('img',
                                         'vtex-store-components-3-x-thumbImg')]

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
                part_number=part_number,
                picture_urls=picture_urls
            )

            return [p]
