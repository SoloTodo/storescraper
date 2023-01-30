from decimal import Decimal
from storescraper.categories import AIR_CONDITIONER, ALL_IN_ONE, CELL, \
    HEADPHONES, MONITOR, NOTEBOOK, OVEN, REFRIGERATOR, STEREO_SYSTEM, \
    WASHING_MACHINE
from storescraper.stores.peru_stores import PeruStores


class Promart(PeruStores):
    base_url = 'https://www.promart.pe'
    params = 'fq=B:762&PS=28&sl=3dfc2a1e-3b52-4d11-9dbd-48bf2b008386&cc=28&s' \
        'm=0&O=OrderByScoreDESC'
    product_container_class = 'product'

    categories_json = {
        'parlantes': STEREO_SYSTEM,
        'equipos de sonido': STEREO_SYSTEM,
        'laptops': NOTEBOOK,
        'celulares y smartphones': CELL,
        'computadoras de escritorio': ALL_IN_ONE,
        'refrigeradoras': REFRIGERATOR,
        'lavadoras': WASHING_MACHINE,
        'lavaseca': WASHING_MACHINE,
        'secadoras de ropa': WASHING_MACHINE,
        'cocinas de pie': OVEN,
        'hornos microondas': OVEN,
        'aire acondicionado': AIR_CONDITIONER,
        'audífonos': HEADPHONES,
        'monitores': MONITOR,
    }

    @classmethod
    def get_offer_price(cls, session, sku, normal_price, store_seller):
        payload = {
            "items": [{"id": sku, "quantity": 1, "seller": "1"}],
            "country": "PER",
        }
        offer_info = session.post('https://www.promart.pe/api/checkout/pu'
                                  'b/orderforms/simulation?sc=1', json=payload
                                  ).json()
        if offer_info['ratesAndBenefitsData']:
            teaser = offer_info['ratesAndBenefitsData']['teaser']
            if len(teaser) != 0:
                discount = teaser[0]['effects']['parameters'][-1]['value']
                offer_price = (normal_price - Decimal(discount)).quantize(0)
            else:
                offer_price = normal_price
        else:
            offer_price = normal_price

        return offer_price
