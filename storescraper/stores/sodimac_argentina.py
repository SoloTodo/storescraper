import json

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class SodimacArgentina(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'AirConditioner',
            'WaterHeater',
            'WashingMachine',
            'Stove',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['cat1730006/Heladeras', 'Refrigerator'],
            ['cat20630/Aires-Acondicionados', 'AirConditioner'],
            ['cat20528/Calefones', 'WaterHeater'],
            ['cat260052/Lavarropas', 'WashingMachine'],
            ['cat20592/Hornos-Empotrados', 'Stove'],
            ['cat20590/Anafes,-hornos-y-cocinas', 'Stove'],
            ['cat270040/Cocinas-a-gas', 'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 0

            while True:
                url = 'http://www.sodimac.com.ar/sodimac-ar/category/{}/' \
                      'N-1z141x3?No={}'.format(category_path, page)
                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                mosaic_divs = soup.findAll('div', 'informationContainer')

                if not mosaic_divs:
                    if page == 0:
                        raise Exception('No products for {}'.format(url))
                    break

                for div in mosaic_divs:
                    product_url = 'http://www.sodimac.com.ar' + \
                                  div.find('a')['href']
                    product_url = product_url.replace(' ', '')
                    product_urls.append(product_url)
                page += 16

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if 'empty=true' in response.url:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        prices_box = soup.find('section', 'prices-box')
        if not prices_box:
            return []

        sku = soup.find('input', {'id': 'currentProductId'})['value'].strip()

        model = soup.find('h1', 'name').text
        brand = soup.find('h2', 'brand').text

        name = '{} {}'.format(brand, model)

        part_number = None

        specs_table = soup.find('table', 'prod-ficha')
        if specs_table:
            for row in specs_table.findAll('tr')[1:]:
                spec_label = row.find('td').text.strip().lower()
                if spec_label == 'modelo':
                    part_number = row.findAll('td')[1].text.strip()
                    break

        unavailability = soup.find('div', {'id': 'MailNoDisponiblePP'})
        if unavailability:
            stock = 0
        else:
            stock = -1

        op_unica_cmr = bool(prices_box.findAll('span', 'cmr-icon'))

        if op_unica_cmr:
            # CMR Price
            price_container = soup.find('p', 'price')
            offer_price = Decimal(remove_words(
                price_container.text.split('\xa0')[0]))

            # Normal price

            normal_price = None

            sale_price_container = soup.findAll('p', 't-gray')
            for sale_price in sale_price_container:
                price_label = sale_price.getText()
                if 'Precio' in price_label:
                    normal_price = price_label.split('\xa0')[1]
                    normal_price = Decimal(
                        remove_words(normal_price))
                    break

            if not normal_price:
                raise Exception('No normal price found')

        else:
            # Internet Price
            price_container = soup.find('p', 'price')
            normal_price = price_container.text
            normal_price = normal_price.split('\xa0')[0]
            normal_price = Decimal(remove_words(normal_price))
            offer_price = normal_price

        description = html_to_markdown(str(soup.find('section', 'prod-car')))

        # Pictures

        pictures_resource_url = 'http://sodimacar.scene7.com/is/image/' \
                                'SodimacArgentina/{}?req=set,json'.format(sku)
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      session.get(pictures_resource_url).text).groups()[0])

        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'http://sodimacar.scene7.com/is/image/{}?scl=1.0' \
                          ''.format(picture_entry['i']['n'])
            picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'ARS',
            sku=sku,
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
