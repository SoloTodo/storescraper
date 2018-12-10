import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from .movistar import Movistar
from storescraper.utils import remove_words


class MovistarOne(Movistar):
    portability_choices = [
        (3, ''),
    ]
    movistar1 = 1

    @classmethod
    def categories(cls):
        return [
            'Cell'
        ]

    @classmethod
    def _assemble_postpago_cells(cls, json_response, name, url, sku, color_id,
                                 plan_id, portability_suffix):
        if not json_response['current']['movistar1']:
            return []

        soup = BeautifulSoup(json_response['offer'], 'html.parser')
        products = []
        price = Decimal(remove_words(
            soup.find('div', 'price').contents[2]))
        monthly_payment_text = \
            soup.find('div', 'cuotes').text
        monthly_payment_match = re.search(
            r'\$([\d|.]+)', monthly_payment_text)
        monthly_payment = Decimal(
            remove_words(monthly_payment_match.groups()[0]))

        products.append(Product(
            name,
            cls.__name__,
            'Cell',
            url,
            url,
            '{} - {} - {}{}'.format(sku, color_id, plan_id,
                                    portability_suffix),
            -1,
            price,
            price,
            'CLP',
            sku=sku,
            cell_plan_name='{}{}'.format(
                plan_id, portability_suffix),
            cell_monthly_payment=monthly_payment
        ))

        return products
