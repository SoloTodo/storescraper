from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy

import json


class SamsungChile(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'OpticalDiskPlayer',
            'StereoSystem',
            'Cell',
            'Tablet',
            'Refrigerator',
            'Oven',
            'WashingMachine',
            'VacuumCleaner',
            'Monitor',
            'CellAccesory',
            'Headphones',
            'Smartwatch',
            'AirConditioner',
            'DishWasher'

        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_info = cls._category_info()

        urls = []

        for category_id, category_filters, category_path, local_category \
                in category_info:
            if local_category != category:
                continue

            url = 'https://www.samsung.com/cl/{}'.format(category_path)
            urls.append(url)

        return urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        category_info = cls._category_info()
        session = session_with_proxy(extra_args)

        api_url = 'https://searchapi.samsung.com/productfinderGlobal?' \
                  'siteCd=cl&' \
                  'start=0&' \
                  'num=1000&' \
                  'stage=live&' \
                  'onlyFilterInfoYN=N'

        for category_id, category_filters, category_path, category_name \
                in category_info:
            if category_path in url:
                api_url += '&type={}{}'.format(category_id, category_filters)
                break

        if not api_url:
            return []

        products = []
        json_data = json.loads(session.get(api_url).text)['response']
        product_list = json_data['resultData']['productList']

        for product in product_list:
            for model in product['modelList']:
                name = model['displayName']
                model_url = 'https://www.samsung.com{}'.format(model['pdpUrl'])
                key = model['modelCode']
                picture_urls = ['https://images.samsung.com/'
                                'is/image/samsung/{}'
                                .format(model['thumbUrl'])]

                for picture in model['galleryImage']:
                    picture_urls.append(
                        'https://images.samsung.com/is/image/samsung/{}'
                        .format(picture))

                products.append(Product(
                    '{} ({})'.format(name, key),
                    cls.__name__,
                    category,
                    model_url,
                    url,
                    key,
                    -1,
                    Decimal(0),
                    Decimal(0),
                    'CLP',
                    picture_urls=picture_urls
                ))

        return products

    @classmethod
    def _category_info(cls):
        return [
            ('19010000', '', 'tvs/all-tvs', 'Television'),
            ('19020000', '&filter1=02z05',
             'audio-video/blu-ray-dvd-player', 'OpticalDiskPlayer'),
            ('19020000', '&filter1=02z03',
             'audio-video/home-entertainment-system', 'SteroSystem'),
            ('19020000', '&filter1=02z02',
             'audio-video/soundbar', 'StereoSystem'),
            ('18010000', '', 'smartphones/all-smartphones', 'Cell'),
            ('18020000', '', 'tablets/all-tablets', 'Tablet'),
            ('07010000', '', 'refrigerators/all-refrigerators',
             'Refrigerator'),
            ('07180000', '&filter1=01z01',
             'cooking-appliances/microwave-ovens', 'Oven'),
            ('07170000', '', 'washing-machines/all-washing-machines',
             'WashingMachine'),
            ('07070000', '', 'vacuum-cleaners/all-vacuum-cleaners',
             'VacuumCleaner'),
            ('21030000', '', 'monitors/all-monitors', 'Monitor'),
            ('18060000', '&filter1=01z07', 'mobile-accessories/others',
             'CellAccesory'),
            ('18060000', '&filter1=01z01',
             'mobile-accessories/all-mobile-accessories/?cases',
             'CellAccesory'),
            ('18060000', '&filter1=01z04', 'mobile-accessories/power',
             'CellAccesory'),
            ('18080000', '', 'mobile-iot/all-mobile-iot', 'CellAccesory'),
            ('18030000', '&filter1=01z04%2B01z05',
             'wearables/all-wearables/?gear-vr+camera', 'CellAccesory'),
            ('18060000', '&filter1=01z02', 'mobile-accessories/audio',
             'Headphones'),
            ('18030000', '&filter1=01z06', 'wearables/all-wearables/?earables',
             'Headphones'),
            ('18030000', '&filter1=01z02%2B01z03',
             'wearables/all-wearables/?smartwatch+sport-band', 'Smartwatch'),
            ('07190000', '', 'air-conditioners/all-air-conditioners',
             'AirConditioner'),
            ('07180000', '&filter1=01z02', 'cooking-appliances/dishwashers',
             'DishWasher'),
        ]
