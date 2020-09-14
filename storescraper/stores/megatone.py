import json

import re

import demjson
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Megatone(Store):
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
            [('61', '36,35,34,'), 'Refrigerator'],
            [('48', '246,63,205,245,64,172,'), 'AirConditioner'],
            [('66', '28,26,27,'), 'WaterHeater'],
            [('6', '38,39,37,'), 'WashingMachine'],
            [('55', '31,241,29,30,'), 'Stove'],
            [('57', '25,'), 'Stove'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow: ' + page)

                request_params = {
                    'idMenu': category_path[0],
                    'paginaActual': str(page),
                    'familiasBuscadas': category_path[1],
                    'filtroCategorias': '',
                    'filtroGeneros': '',
                    'filtroPlataformas': '',
                    'filtroMarcas': '',
                    'filtroPrestadoras': '',
                    'filtroPrecios': '',
                    'filtroOfertas': '0',
                    'palabraBuscada': '',
                    'menorPrecioMultiploDe10': '',
                    'intervaloPrecios': '',
                    'tipoListado': 'Grilla',
                    'orden': '0',
                    'productosBuscados': '',
                    'filtroCuotas': ''
                }

                request_params = json.dumps(request_params)
                session.headers['Content-Type'] = 'application/json'
                response = session.post(
                    'https://www.megatone.net/Listado.aspx/CargarMas',
                    request_params)

                raw_json = json.loads(response.text)['d']['_HTMLProductos']
                soup = BeautifulSoup(raw_json, 'html.parser')

                containers = soup.findAll('div', 'itemListadoGrilla')[::2]

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_path)
                    break

                for container in containers:
                    product_url = 'https://www.megatone.net' + \
                                  container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        brand = soup.find('span', {'id': 'MainContent_lblMarca'}).text.strip()
        model = soup.find('span', {'id': 'MainContent_lblNombre'}).text.strip()
        name = '{} {}'.format(brand, model)

        product_data = re.search(r'var google_tag_params = ([\s\S]+?);',
                                 page_source).groups()[0]
        product_json = demjson.decode(product_data)

        price = Decimal(product_json['ecomm_totalvalue'])
        sku = product_json['ecomm_prodid']

        description = html_to_markdown(
            str(soup.find('div', {'id': 'DivDescripcion'})))

        picture_urls = []

        for tag in soup.findAll('a', 'imgThumb'):
            try:
                picture_url = tag['data-image'].replace(' ', '%20')
                picture_urls.append(picture_url)
            except KeyError:
                pass

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'ARS',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
