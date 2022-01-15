from storescraper.categories import CELL, WEARABLE, TELEVISION, STEREO_SYSTEM, \
    NOTEBOOK, MONITOR, EXTERNAL_STORAGE_DRIVE, TABLET, HEADPHONES, MOUSE, \
    GAMING_CHAIR, WASHING_MACHINE, REFRIGERATOR, OVEN, AIR_CONDITIONER
from storescraper.utils import session_with_proxy

from .travel_tienda import TravelTienda


class TravelTiendaFull(TravelTienda):
    @classmethod
    def categories(cls):
        return [
            CELL,
            WEARABLE,
            STEREO_SYSTEM,
            TELEVISION,
            NOTEBOOK,
            MONITOR,
            EXTERNAL_STORAGE_DRIVE,
            TABLET,
            HEADPHONES,
            MOUSE,
            GAMING_CHAIR,
            WASHING_MACHINE,
            REFRIGERATOR,
            OVEN,
            AIR_CONDITIONER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ('3842720512', CELL),
            ('444586937', WEARABLE),
            ('2234300147', STEREO_SYSTEM),
            ('2722336774', TELEVISION),
            ('3415774358', NOTEBOOK),
            ('375810843', MONITOR),
            ('2306324657', EXTERNAL_STORAGE_DRIVE),
            ('2934181475', TABLET),
            ('1226813193', HEADPHONES),
            ('2547146328', MOUSE),
            ('714969430', GAMING_CHAIR),
            ('326296390', STEREO_SYSTEM),
            ('3121709090', HEADPHONES),
            ('1345767085', STEREO_SYSTEM),
            ('1095159098', STEREO_SYSTEM),
            ('3514911626', STEREO_SYSTEM),
            ('3551610308', STEREO_SYSTEM),
            ('2620100069', WASHING_MACHINE),
            ('306745319', REFRIGERATOR),
            ('394354836', WASHING_MACHINE),
            ('831669398', OVEN),
            ('628735343', AIR_CONDITIONER),
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        print(category)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url_webpage = 'https://tienda.travel.cl/ccstore/v1/assembler/' \
                          'pages/Default/osf/catalog/_/N-{}?Nrpp=1000' \
                          '&Nr=AND%28sku.availabilityStatus%3AINSTOCK%29' \
                          ''.format(category_path)
            response = session.get(url_webpage)
            json_data = response.json()
            for product_entry in json_data['results']['records']:
                product_path = product_entry['attributes']['product.route'][0]
                product_url = 'https://tienda.travel.cl' + product_path
                print(product_url)
                product_urls.append(product_url)
        return product_urls
