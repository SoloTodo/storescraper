from decimal import Decimal


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
            'COL': cls('$', '.', ',', 0),
            'MXN': cls('$', '.', ',', 2),
            'PEN': cls('S/', '.', ',', 2),
            'USD': cls('$', ',', '.', 2),
        }

        currency = known_codes[code]

        return cls._format_currency(
            value, currency.prefix, currency.thousands_separator,
            currency.decimal_separator, places=currency.decimal_places)

    @staticmethod
    def _format_currency(value, curr='', sep='.', dp=',',
                         pos='', neg='-', trailneg='', places=0):
        """Convert Decimal to a money formatted string.

        curr: optional currency symbol before the sign (may be blank)
        sep: optional grouping separator (comma, period, space, or blank)
        dp: decimal point indicator (comma or period)
        only specify as blank when places is zero
        pos: optional sign for positive numbers: '+', space or blank
        neg: optional sign for negative numbers: '-', '(', space or blank
        trailneg:optional trailing minus indicator: '-', ')', space or blank
        places: Number of decimal places to consider
        """

        quantized_precision = Decimal(10) ** -places  # 2 places --> '0.01'
        sign, digits, exp = value.quantize(quantized_precision).as_tuple()
        result = []
        digits = list(map(str, digits))
        build, iter_next = result.append, digits.pop

        if sign:
            build(trailneg)
        for i in range(places):
            build(iter_next() if digits else '0')
        if places:
            build(dp)
        if not digits:
            build('0')
        i = 0
        while digits:
            build(iter_next())
            i += 1
            if i == 3 and digits:
                i = 0
                build(sep)
        build(curr)
        build(neg if sign else pos)

        return ''.join(reversed(result))
