# coding=utf-8
import urllib
from decimal import Decimal

import re

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Magens(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'VideoCard',
            'Processor',
            'Monitor',
            'Television',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'CpuCooler',
            'Tablet',
            'Printer'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['Procesadores', 'Processor'],
            ['Placa%20Madre', 'Motherboard'],
            ['Memoria%20Ram', 'Ram'],
            ['Almacenamiento', 'StorageDrive'],
            ['Tarjeta%20de%20Video', 'VideoCard'],
            # ['Partes%20y%20Piezas?tipoGrilla=V&orden=&&marca=&precioMinimo=-1'
            #  '&precioMaximo=-1&atributos=tipo_de_producto:GABINETE',
            #  'ComputerCase'],
            # ['Partes%20y%20Piezas?tipoGrilla=V&orden=&marca=&'
            #  'precioMinimo=-1&precioMaximo=-1&atributos=tipo_de_producto:'
            #  'FUENTE%20DE%20PODER%20PC;FUENTE%20DE%20PODER;', 'PowerSupply'],
            ['Notebook', 'Notebook'],
            ['Tablet', 'Tablet'],
            ['Pantalla', 'Monitor'],
            ['Monitor', 'Monitor'],
            ['Televisores', 'Television'],
            # ['Impresora%20Láser', 'Printer'],
            ['Impresora%20De%20Inyección%20De%20Tinta', 'Printer'],
            ['Impresora', 'Printer'],
        ]

        discovered_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1
            found_products = 0

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                separator = '?'
                if '?' in url_extension:
                    separator = '&'

                category_url = 'http://www.magens.cl/Categoria/' \
                               '{}{}paginaActual={}'.format(
                                url_extension, separator, page)

                soup = BeautifulSoup(
                    session.get(category_url).text, 'html.parser')

                product_containers = soup.findAll('article', 'product-block')

                if not product_containers:
                    if page == 1:
                        raise Exception('Empty category path: {} - {}'.format(
                            category, url_extension))
                    else:
                        break

                for container in product_containers:
                    product_url = container.find('a')['href'].replace('\t', '')
                    discovered_urls.append(product_url)
                    found_products += 1

                page += 1

            if not found_products:
                raise Exception('No products found for: {}'.format(
                    url_extension))

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        cleaned_url = urllib.parse.unquote(url).encode(
            'ascii', 'ignore').decode('ascii')
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(cleaned_url).text, 'html.parser')

        part_number = soup.find(
            'small', 'product-info__part-number').string.split(':')[1].strip()

        name = soup.find(
            'meta', {'property': 'og:description'})['content'].strip()

        sku = re.search(r'-(\d+)/p', url).groups()[0]

        description = ''

        for panel_id in ['panel_fichaTecnica', 'panel_atributos']:
            panel = soup.find('section', {'id': panel_id})
            if panel:
                description += html_to_markdown(str(panel)) + '\n\n'

        if soup.find('button', {'id': 'product-form__add-to-cart'}):
            stock = -1
        else:
            stock = 0

        offer_price = soup.find('span', 'product-info__price-current')
        offer_price = offer_price.text.split('$')[1]
        offer_price = Decimal(remove_words(offer_price))

        normal_price = soup.find('span', 'product-info__price-normal')
        normal_price = normal_price.text.split('$')[1]
        normal_price = Decimal(remove_words(normal_price))

        picture_tags = soup.find('div', {'id': 'product-slider'})\
            .findAll('img', 'product-slider__block-image')

        picture_urls = [p['src'].replace(' ', '%20') for p in picture_tags]

        product = Product(
            name,
            cls.__name__,
            category,
            cleaned_url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            part_number=part_number,
            sku=sku,
            description=description,
            cell_plan_name=None,
            cell_monthly_payment=None,
            picture_urls=picture_urls
        )

        return [product]
