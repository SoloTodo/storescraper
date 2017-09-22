import importlib
from decimal import Decimal

import html2text
import re

CLP_BLACKLIST = ['CLP$', 'precio', 'internet', 'normal',
                 '$', '.', ',', '&nbsp;', '\r', '\n', '\t']


def remove_words(text, blacklist=CLP_BLACKLIST):
    for word in blacklist:
        text = text.replace(word, '')

    return text


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_store_class_by_name(store_class_name):
    store_module = importlib.import_module('storescraper.stores')
    return getattr(store_module, store_class_name)


def format_currency(value, curr='', sep='.', dp=',',
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


def html_to_markdown(html, baseurl=''):
    h = html2text.HTML2Text(baseurl=baseurl)
    h.body_width = 0
    result = h.handle(html)

    def strip_bold_content(match):
        return ' **{}** '.format(match.groups()[0].strip())

    result = re.sub(r'\*\*(.+?)\*\*', strip_bold_content, result)

    return result
