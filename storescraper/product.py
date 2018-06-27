import json
from datetime import datetime
from decimal import Decimal
import dateutil.parser
import validators

import pytz

from .utils import check_ean13
from .currency import Currency


class Product:
    VALID_CONDITIONS = [
        'https://schema.org/DamagedCondition',
        'https://schema.org/NewCondition',
        'https://schema.org/RefurbishedCondition',
        'https://schema.org/UsedCondition',
    ]

    def __init__(self, name, store, category, url, discovery_url, key,
                 stock, normal_price, offer_price, currency, part_number=None,
                 sku=None, ean=None, description=None, cell_plan_name=None,
                 cell_monthly_payment=None, picture_urls=None, timestamp=None,
                 condition='https://schema.org/NewCondition'):
        assert isinstance(key, str)
        assert isinstance(stock, int)
        assert len(name) <= 256
        assert len(key) <= 256
        assert offer_price <= normal_price

        if cell_plan_name:
            assert len(cell_plan_name) <= 50

        if picture_urls:
            for picture_url in picture_urls:
                assert validators.url(picture_url), picture_url

        if ean:
            assert check_ean13(ean), ean

        assert condition in Product.VALID_CONDITIONS

        self.name = name
        self.store = store
        self.category = category
        self.url = url
        self.discovery_url = discovery_url
        self.key = key
        self.stock = stock
        self.normal_price = normal_price
        self.offer_price = offer_price
        self.currency = currency
        self.part_number = part_number
        self.sku = sku
        self.ean = ean
        self.description = description
        self.cell_plan_name = cell_plan_name
        self.cell_monthly_payment = cell_monthly_payment
        self.picture_urls = picture_urls
        if not timestamp:
            timestamp = datetime.utcnow()
        if not timestamp.tzinfo:
            timestamp = pytz.utc.localize(timestamp)
        self.condition = condition
        self.timestamp = timestamp

    def __str__(self):
        lines = list()
        lines.append('{} - {} ({})'.format(self.store, self.name,
                                           self.category))
        lines.append(self.url)
        lines.append('Discovery URL: {}'.format(self.discovery_url))
        lines.append('SKU: {}'.format(
            self.optional_field_as_string('sku')))
        lines.append('EAN: {}'.format(
            self.optional_field_as_string('ean')))
        lines.append('Part number: {}'.format(
            self.optional_field_as_string('part_number')))
        lines.append('Picture URLs: {}'.format(
            self.optional_field_as_string('picture_urls')))
        lines.append(u'Key: {}'.format(self.key))
        lines.append(u'Stock: {}'.format(self.stock_as_string()))
        lines.append(u'Currency: {}'.format(self.currency))
        lines.append(u'Normal price: {}'.format(Currency.format(
            self.normal_price, self.currency)))
        lines.append(u'Offer price: {}'.format(Currency.format(
            self.offer_price, self.currency)))
        lines.append('Condition: {}'.format(self.condition))
        lines.append('Cell plan name: {}'.format(
            self.optional_field_as_string('cell_plan_name')))

        cell_monthly_payment = self.cell_monthly_payment

        if cell_monthly_payment is None:
            cell_monthly_payment_string = 'N/A'
        else:
            cell_monthly_payment_string = Currency.format(
                cell_monthly_payment, self.currency)

        lines.append('Cell monthly payment: {}'.format(
            cell_monthly_payment_string))
        lines.append('Timestamp: {}'.format(self.timestamp.isoformat()))

        lines.append('Description: {}'.format(
            self.optional_field_as_string('description')[:30]))

        return '\n'.join(lines)

    def __repr__(self):
        return '{} - {}'.format(self.store, self.name)

    def serialize(self):
        serialized_cell_monthly_payment = str(self.cell_monthly_payment) \
            if self.cell_monthly_payment is not None else None

        return {
            'name': self.name,
            'store': self.store,
            'category': self.category,
            'url': self.url,
            'discovery_url': self.discovery_url,
            'key': self.key,
            'stock': self.stock,
            'normal_price': str(self.normal_price),
            'offer_price': str(self.offer_price),
            'currency': self.currency,
            'part_number': self.part_number,
            'sku': self.sku,
            'ean': self.ean,
            'description': self.description,
            'cell_plan_name': self.cell_plan_name,
            'cell_monthly_payment': serialized_cell_monthly_payment,
            'picture_urls': self.picture_urls,
            'timestamp': self.timestamp.isoformat(),
            'condition': self.condition,
        }

    @classmethod
    def deserialize(cls, serialized_data):
        serialized_data['normal_price'] = \
            Decimal(serialized_data['normal_price'])
        serialized_data['offer_price'] = \
            Decimal(serialized_data['offer_price'])

        cell_monthly_payment = serialized_data['cell_monthly_payment']
        if cell_monthly_payment:
            cell_monthly_payment = Decimal(cell_monthly_payment)

        serialized_data['cell_monthly_payment'] = cell_monthly_payment

        serialized_data['timestamp'] = \
            dateutil.parser.parse(serialized_data['timestamp'])
        return cls(**serialized_data)

    def is_available(self):
        return self.stock != 0

    ##########################################################################
    # Utility methods
    ##########################################################################

    def stock_as_string(self):
        if self.stock == -1:
            return 'Available but unknown'
        elif self.stock == 0:
            return 'Unavailable'
        else:
            return str(self.stock)

    def optional_field_as_string(self, field):
        field_value = getattr(self, field)
        if field_value is not None:
            return field_value
        else:
            return 'N/A'

    def picture_urls_as_json(self):
        if not self.picture_urls:
            return None
        return json.dumps(self.picture_urls)
