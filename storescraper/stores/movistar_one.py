import json
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, session_with_proxy


class MovistarOne(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category == 'Cell':
            return ['https://ww2.movistar.cl/movistarone/productos.json']
        return []

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        json_data = json.loads(session.get(url).text)
        products = []

        plans_dict = {
            'Plan Libre': 'Movistar con Todo Libre Cod_0P8_Porta cuotas',
            'Plan XL': 'Movistar con Todo XL Cod_0O0_Porta cuotas',
            'Plan L': 'Movistar con Todo L Cod_0O4_Porta cuotas',
            'Plan M': 'Plus M Cod_OCE_Porta cuotas',
        }

        for entry in json_data:
            name = entry['telefono']
            picture_urls = ['https://ww2.movistar.cl/movistarone/' +
                            entry['imagenUrl'].replace(' ', '%20')]

            for plan_entry in entry['planes']:
                cell_plan_name = plans_dict[plan_entry['tipoPlan']]

                price = Decimal(remove_words(plan_entry['pieEquipo']))
                cell_monthly_payment = Decimal(
                    remove_words(plan_entry['cuotaMensualEquipo']))

                products.append(Product(
                    name,
                    cls.__name__,
                    'Cell',
                    'https://ww2.movistar.cl/movistarone/',
                    url,
                    '{} {}'.format(name, cell_plan_name),
                    -1,
                    price,
                    price,
                    'CLP',
                    picture_urls=picture_urls,
                    cell_plan_name=cell_plan_name,
                    cell_monthly_payment=cell_monthly_payment
                ))

        return products
