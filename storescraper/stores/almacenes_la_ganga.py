import logging
import re

from decimal import Decimal
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import TELEVISION, AIR_CONDITIONER, \
    WASHING_MACHINE, STEREO_SYSTEM, REFRIGERATOR, OVEN


class AlmacenesLaGanga(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            AIR_CONDITIONER,
            WASHING_MACHINE,
            STEREO_SYSTEM,
            REFRIGERATOR,
            OVEN
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['Televisores', 'Television'],
            ['Aires-Split', 'AirConditioner'],
            ['Lavadoras', 'WashingMachine'],
            ['Equipos-de-sonido', 'StereoSystem'],
            ['Refrigeradoras', 'Refrigerator'],
            ['Cocinas', 'Oven']
        ]

        session = session_with_proxy(extra_args)
        base_url = 'https://www.almaceneslaganga.com/' \
                   'pedidos-en-linea/efectivo/{}/LG'
        product_urls = []

        for url_extension, local_category in category_paths:
            if category != local_category:
                continue

            url = base_url.format(url_extension)
            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            products = soup.findAll('div', 'esquema_producto')

            if not products:
                logging.warning('Empty path: ' + url)

            for product in products:
                product_slug = product.find(
                    'button', 'btn-detalles')['producto']
                product_url = 'https://www.almaceneslaganga.com/' \
                              'pedidos-en-linea/efectivo/{}'\
                    .format(product_slug)
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        page_source = response.text

        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('div', {'id': 'nombre_producto_detalles_tecnicos'})\
            .text.strip()
        sku = re.search(
            r'global_id_producto="([\S\s]+?)";', page_source).groups()[0]
        part_number = re.search(
            r'\[modelo] => ([\S\s]+?)\n', page_source).groups()[0]
        stock = -1

        price = Decimal(
            soup.find('label', {'id': 'precio_detalles_tecnicos'})
                .text.replace('$', '').replace(',', ''))

        picture_url_base = 'https://www.almaceneslaganga.com/pedidos-en-linea'
        picture_urls = [
            a['src'].replace('..', picture_url_base)
            for a in soup.findAll('img', 'galeria_detalles_tecnicos')]

        description = html_to_markdown(
            str(soup.find('label', {'id': 'descripcion_detalles_tecnicos'})))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'USD',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
