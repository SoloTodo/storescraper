from collections import defaultdict

from .mercado_libre_chile import MercadoLibreChile


class MercadoLibreLg(MercadoLibreChile):
    store_extension = '_Tienda_lg'

    @classmethod
    def _category_paths(cls):
        return {'_Tienda_lg': [
            ('audio', 'StereoSystem'),
            ('electronica/televisores', 'Television'),
            ('electrodomesticos/refrigeracion', 'Refrigerator'),
            ('lavado', 'WashingMachine'),
            ('celulares-telefonia', 'Cell'),
            ('computacion', 'Monitor'),
        ]}

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        product_urls = cls.discover_urls_for_category(category, extra_args)
        product_entries = defaultdict(lambda: [])

        sections_dict = {
            'StereoSystem': 'Audio',
            'Television': 'Televisores',
            'Refrigerator': 'Refrigeración',
            'WashingMachine': 'Lavado',
            'Cell': 'Celulares y Telefonía',
            'Monitor': 'Computación',
        }

        section_name = sections_dict[category]

        for idx, product_url in enumerate(product_urls):
            product_entries[product_url].append({
                'category_weight': 1.0,
                'section_name': section_name,
                'value': idx + 1
            })

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        # Remove the seller because we consider MecadoLibreLg to be a
        # standalone retailer, in particular because the LG WTB system
        # only displays entries without a seller (not from marketplaces)
        # and we want to consider MercadoLibreLG for that.
        products = super().products_for_url(
            url, category=category, extra_args=extra_args)

        for product in products:
            product.seller = None

        return products
