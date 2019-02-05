from bs4 import BeautifulSoup
from decimal import Decimal
import json

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class ClubSmart(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Television',
            'Refrigerator',
            'WashingMachine',
            'VacuumCleaner',
            'Headphones',
            'Wearable',
            'AirConditioner',
            'DishWasher',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('mobile/Smartphone', 'Cell'),
            ('mobile/Smartwatch', 'Wearable'),
            ('mobile/Audifono', 'Headphones'),
            ('tv-y-audio/Televisor%20LED', 'Television'),
            ('linea-blanca/Refrigerador', 'Refrigerator'),
            ('linea-blanca/Lavadora', 'WashingMachine'),
            ('linea-blanca/Aspiradora', 'VacuumCleaner'),
            ('linea-blanca/Aire%20Acondicionado', 'AirConditioner'),
            ('linea-blanca/Lavavajillas', 'DishWasher')
        ]

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            url = 'https://www.clubsmart.cl/api/catalog_system/pub/products/' \
                  'search/{}?map=c,specificationFilter_40&_from=0&_to=49&' \
                  'O=OrderByPriceDESC&sc=1'.format(category_path)

            product_urls.append(url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        c_url = 'https://www.clubsmart.cl/clubsmart/dataentities/CL/search?_' \
                'where=email={}&_fields=id,email,bCluster,bReferralCode' \
            .format(extra_args['mail'])
        data = session.get(c_url)
        cookie = 'CL-' + json.loads(data.text)[0]['id']

        data = session.get(url, cookies={'loginProfile': cookie})
        json_data = json.loads(data.text)

        products = []

        for product in json_data:
            name = product['productName']
            sku = product['productReference']
            product_url = product['link']
            stock = product['items'][0]['sellers'][0][
                'commertialOffer']['AvailableQuantity']
            price = Decimal(product['items'][0]['sellers'][0]
                            ['commertialOffer']['Price'])

            pictures = product['items'][0]['images']
            picture_urls = []

            for picture in pictures:
                picture_urls.append(picture['imageUrl'])

            description = html_to_markdown(product['description'])

            p = Product(
                name,
                cls.__name__,
                category,
                product_url,
                url,
                sku,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)

        return products
