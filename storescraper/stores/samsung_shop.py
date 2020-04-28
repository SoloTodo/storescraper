from decimal import Decimal
import json

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class SamsungShop(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

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
            'Tablet',
            'Oven',
            'CellAccesory',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('mobile/accesorios', 'Headphones'),
            ('mobile/smartphones', 'Cell'),
            ('mobile/tablets', 'Tablet'),
            ('mobile/wearables', 'Wearable'),
            ('tv-y-audio/accesorios-tv', 'CellAccesory'),
            ('tv-y-audio/audio-y-video', 'StereoSystem'),
            ('tv-y-audio/tv', 'Television'),
            ('linea-blanca/accesorios', 'CellAccesory'),
            ('linea-blanca/aires-acondicionados', 'AirConditioner'),
            ('linea-blanca/aspiradoras', 'VacuumCleaner'),
            ('linea-blanca/empotrados', 'Oven'),
            ('linea-blanca/lavadoras---secadoras', 'WashingMachine'),
            ('linea-blanca/microondas', 'Oven'),
            ('linea-blanca/refrigeradores', 'Refrigerator'),
            ('linea-blanca/lavavajillas', 'DishWasher'),
        ]

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            url = 'https://shop.samsung.cl/api/catalog_system/pub/products/' \
                  'search/{}?map=c,c,specificationFilter_226'\
                .format(category_path)

            product_urls.append(url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        # &_from=0&_to=49
        session = session_with_proxy(extra_args)

        page = 0
        page_size = 50
        products = []

        while True:
            target_url = '{}&_from={}&_to={}'.format(
                url, page*page_size, (page + 1) * page_size - 1
            )
            data = session.get(target_url)

            json_data = json.loads(data.text)

            if not json_data:
                if page == 0:
                    raise Exception('Empty category: ' + target_url)
                break

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
                    part_number=product['productReference'],
                    description=description,
                    picture_urls=picture_urls
                )

                products.append(p)
            page += 1

        return products
