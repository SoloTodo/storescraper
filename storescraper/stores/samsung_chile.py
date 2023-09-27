from decimal import Decimal

from storescraper.categories import NOTEBOOK, CELL, TABLET, WEARABLE, \
    HEADPHONES, CELL_ACCESORY, TELEVISION, STEREO_SYSTEM, REFRIGERATOR, \
    WASHING_MACHINE, OVEN, DISH_WASHER, VACUUM_CLEANER, AIR_CONDITIONER, \
    MONITOR
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy

import json


class SamsungChile(StoreWithUrlExtensions):
    url_extensions = [
        ('01010000', CELL),
        ('01020000', TABLET),
        ('01030000', WEARABLE),
        ('01040000', HEADPHONES),
        ('01050000', CELL_ACCESORY),
        ('04010000', TELEVISION),
        ('05010000', STEREO_SYSTEM),
        ('08030000', REFRIGERATOR),
        ('08010000', WASHING_MACHINE),
        ('08110000', OVEN),
        ('08090000', DISH_WASHER),
        ('08070000', VACUUM_CLEANER),
        ('08050000', AIR_CONDITIONER),
        ('08080000', OVEN),
        ('07010000', MONITOR),
        ('03010000', NOTEBOOK),
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        return [url_extension]

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        RESULTS_PER_PAGE = 100
        api_url = ('https://searchapi.samsung.com/v6/front/b2c/product/'
                   'finder/newhybris?siteCode=cl&num={}'
                   '&onlyFilterInfoYN=N'.format(RESULTS_PER_PAGE))

        products = []

        for category_id, category_name in cls.url_extensions:
            if category_name != category:
                continue

            offset = 0
            while True:
                if offset > RESULTS_PER_PAGE * 10:
                    raise Exception('Page overflow')

                category_endpoint = api_url + '&type={}&start={}'.format(
                    category_id, offset)
                print(category_endpoint)

                response = session.get(category_endpoint)
                json_data = json.loads(response.text)['response']
                product_list = json_data['resultData']['productList']

                if not product_list:
                    if offset == 0:
                        import ipdb
                        ipdb.set_trace()
                        a=5
                    break

                for product in product_list:
                    for model in product['modelList']:
                        name = model['displayName']
                        variant_specs = []

                        for spec_entry in model['fmyChipList']:
                            variant_specs.append(
                                spec_entry['fmyChipName'].strip())

                        if variant_specs:
                            name += ' ({})'.format(' / '.join(variant_specs))

                        if 'www.samsung.com' in model['pdpUrl']:
                            model_url = 'https:{}'.format(model['pdpUrl'])
                        else:
                            model_url = 'https://www.samsung.com{}'\
                                .format(model['pdpUrl'])
                        key = model['modelCode']
                        picture_urls = ['https:' + model['thumbUrl']]

                        for picture in model['galleryImage'] or []:
                            picture_urls.append('https:' + picture)

                        if model['promotionPrice']:
                            price = Decimal(model['promotionPrice'])
                        elif model['priceDisplay']:
                            price = Decimal(model['priceDisplay'])
                        else:
                            price = Decimal(0)
                        price = price.quantize(0)

                        if model['stockStatusText'] == 'inStock':
                            stock = -1
                        else:
                            stock = 0

                        products.append(Product(
                            '{} ({})'.format(name, key),
                            cls.__name__,
                            category,
                            model_url,
                            url,
                            key,
                            stock,
                            price,
                            price,
                            'CLP',
                            sku=key,
                            picture_urls=picture_urls,
                            allow_zero_prices=True
                        ))
                offset += RESULTS_PER_PAGE

        return products
