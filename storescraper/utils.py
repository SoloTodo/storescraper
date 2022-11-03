import functools
import importlib
import logging
from decimal import Decimal

import html2text
import re

import math

import requests
from seleniumwire import webdriver
from selenium.webdriver import DesiredCapabilities


CLP_BLACKLIST = ['CLP$', 'CLP', 'precio', 'internet', 'normal',
                 '$', '.', ',', '&nbsp;', '\r', '\n', '\t', '\xa0']


def remove_words(text, blacklist=CLP_BLACKLIST):
    for word in blacklist:
        text = text.replace(word, '')

    return text


def chunks(a_list, n):
    """Yield successive n-sized chunks from a_list."""
    for i in range(0, len(a_list), n):
        yield a_list[i:i + n]


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


def check_ean13(ean):
    if not ean or not isinstance(ean, str):
        return False
    if len(ean) != 13:
        return False
    try:
        int(ean)
    except Exception:
        return False
    oddsum = 0
    evensum = 0
    eanvalue = ean
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) % 10

    if check != int(ean[-1]):
        return False
    return True


def session_with_proxy(extra_args):
    session = requests.Session()
    session.request = functools.partial(session.request, timeout=30)

    if extra_args and 'proxy' in extra_args:
        proxy = extra_args['proxy']

        session.proxies = {
            'http': proxy,
            'https': proxy,
        }

    return session


CF_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) '
                  'Gecko/20100101 Firefox/84.0'
}


class HeadlessChrome:
    def __init__(self, images_enabled=False, proxy=None, headless=True,
                 timeout=30, user_agent=None):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('headless')
        if not images_enabled:
            options.add_argument('--blink-settings=imagesEnabled=false')
        if user_agent:
            options.add_argument('--user-agent=' + user_agent)

        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches",
                                        ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        seleniumwire_options = {}
        if proxy:
            seleniumwire_options['proxy'] = {
                'http': proxy,
                'https': proxy
            }

        self.driver = webdriver.Chrome(
            chrome_options=options, seleniumwire_options=seleniumwire_options)
        self.driver.set_page_load_timeout(timeout)
        self.driver.header_overrides = CF_REQUEST_HEADERS

    def __enter__(self):
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.close()


def trim(text):
    return ' '.join(text.split())
