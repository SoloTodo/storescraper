from .utils import format_currency


class Currency:
    def __init__(self, prefix, thousands_separador, decimal_separator,
                 decimal_places):
        self.prefix = prefix
        self.thousands_separator = thousands_separador
        self.decimal_separator = decimal_separator
        self.decimal_places = decimal_places

    @classmethod
    def format(cls, value, code):
        known_codes = {
            'ARS': cls('$', '.', ',', 0),
            'BRL': cls('R$', '.', ',', 2),
            'CLP': cls('$', '.', ',', 0),
            'COP': cls('$', '.', ',', 0),
            'MXN': cls('$', '.', ',', 2),
            'PEN': cls('S/', '.', ',', 2),
            'USD': cls('$', ',', '.', 2),
            'GTQ': cls('$', ',', '.', 2),
            'HNL': cls('L.', ',', '.', 2),
            'DOP': cls('$', ',', '.', 2),
            'NIO': cls('C$', ',', '.', 2),
            'CRC': cls('₡', ',', '.', 0),
            'PYG': cls('₲', '.', ',', 0),
            'UYU': cls('$', '.', ',', 0),
            'BOB': cls('Bs. ', ',', '.', 2)
        }

        currency = known_codes[code]

        return format_currency(
            value, currency.prefix, currency.thousands_separator,
            currency.decimal_separator, places=currency.decimal_places)
