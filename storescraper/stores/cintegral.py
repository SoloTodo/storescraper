import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words
from storescraper.categories import NOTEBOOK, ALL_IN_ONE, TABLET, \
    EXTERNAL_STORAGE_DRIVE, SOLID_STATE_DRIVE, MEMORY_CARD, \
    USB_FLASH_DRIVE, PROCESSOR, COMPUTER_CASE, POWER_SUPPLY, MOTHERBOARD, \
    RAM, VIDEO_CARD, MOUSE, PRINTER, HEADPHONES, STEREO_SYSTEM, UPS, MONITOR, \
    KEYBOARD_MOUSE_COMBO, KEYBOARD, GAMING_CHAIR, WEARABLE, \
    STORAGE_DRIVE


class Cintegral(StoreWithUrlExtensions):
    url_extensions = [
        ['109', NOTEBOOK],
        ['110', ALL_IN_ONE],
        ['176', TABLET],
        ['157', PRINTER],
        ['156', PRINTER],
        ['129', PRINTER],
        ['152', PRINTER],
        ['181', STORAGE_DRIVE],
        ['182', EXTERNAL_STORAGE_DRIVE],
        ['183', SOLID_STATE_DRIVE],
        ['184', MEMORY_CARD],
        ['185', USB_FLASH_DRIVE],
        ['116', POWER_SUPPLY],
        ['115', COMPUTER_CASE],
        ['118', RAM],
        ['117', MOTHERBOARD],
        ['114', PROCESSOR],
        ['119', VIDEO_CARD],
        ['96', MONITOR],
        ['122', KEYBOARD_MOUSE_COMBO],
        ['123', MOUSE],
        ['121', KEYBOARD],
        ['161', NOTEBOOK],
        ['163', WEARABLE],
        ['162', TABLET],
        ['164', KEYBOARD],
        ['139', HEADPHONES],
        ['140', STEREO_SYSTEM],
        ['153', GAMING_CHAIR],
        ['86', WEARABLE],
        ['168', VIDEO_CARD],
        ['160', MONITOR],
        ['159', NOTEBOOK],
        ['172', SOLID_STATE_DRIVE],
        ['171', POWER_SUPPLY],
        ['167', MOUSE],
        ['170', MOTHERBOARD],
        ['169', PROCESSOR],
        ['166', GAMING_CHAIR],
        ['178', RAM],
        ['106', NOTEBOOK],
        ['141', UPS],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args=None):
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        page = 1

        while True:
            if page >= 20:
                raise Exception('Page overflow: ' + url_extension)

            payload = ('action=jet_smart_filters&provider=jet-engine/default&'
                       'query[_tax_query_product_cat][]={}&'
                       'settings[lisitng_id]=645&referrer[uri]=/'
                       '?jsf=jet-engine&pagenum={}').format(
                url_extension, page)
            print(payload)

            res = session.post('https://cintegral.cl/wp-admin/admin-ajax.php',
                               payload)
            json_data = res.json()
            soup = BeautifulSoup(json_data['content'], 'html.parser')
            product_tags = soup.findAll('div', 'jet-listing-grid__item')

            if not product_tags:
                break

            for product_tag in product_tags:
                product_url = product_tag.find(
                    'a', 'jet-listing-dynamic-image__link')['href']
                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')

        name = soup.find('h1', 'product_title').text.strip()
        new_key = soup.find('link', {'rel': 'shortlink'})['href'].split(
            '?p=')[-1]
        old_key = re.match(r'https://cintegral.cl/producto/(\d+)',
                           url).groups()[0]

        stock_label_tag = soup.find('span', text='Stock Web:')
        stock_tag = stock_label_tag.next.next
        stock_match = re.search(r'(\d+)', stock_tag.text.strip())
        stock = int(stock_match.groups()[0])

        offer_price_label_tag = soup.find('div', text='Pago transferencia')
        offer_price = Decimal(remove_words(
            offer_price_label_tag.next.next.text))

        normal_price_label_tag = soup.find('div', text='Pago con Tarjeta')
        normal_price = Decimal(
            remove_words(normal_price_label_tag.next.next.text))

        mpn_label_tag = soup.find('span', text='Part Number:')
        if mpn_label_tag:
            part_number = mpn_label_tag.next.next.strip()
        else:
            part_number = None

        description = html_to_markdown(str(
            soup.find('div', 'woocommerce-Tabs-panel--description')))

        picture_urls = [soup.find('meta', {'property': 'og:image'})['content']]

        if 'REACONDICIONADO' in name.upper():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            new_key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=old_key,
            part_number=part_number,
            description=description,
            picture_urls=picture_urls,
            condition=condition
        )

        return [p]
