import json
import urllib

from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class JumboArgentina(Store):
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
        category_ids = [
            ['24965', 'Refrigerator'],
            ['24966', 'Refrigerator'],
            ['24967', 'Refrigerator'],
            ['24940', 'AirConditioner'],
            ['24950', 'WaterHeater'],
            ['24976', 'WashingMachine'],
            ['24977', 'WashingMachine'],
            ['24953', 'Stove'],
            ['24954', 'Stove'],
        ]

        discovery_urls = []
        for category_id, local_category in category_ids:
            if local_category != category:
                continue

            discovery_url = 'https://www.jumbo.com.ar/Comprar/Home.aspx#' \
                            '_atCategory=false&_atGrilla=true&_id=' + \
                            category_id
            discovery_urls.append(discovery_url)

        return discovery_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        category_id = urllib.parse.parse_qs(
            urllib.parse.urlparse(url).fragment)['_id'][0]
        session = session_with_proxy(extra_args)

        params = {
            'IdMenu': category_id,
            'textoBusqueda': "",
            'producto': "",
            'marca': "",
            'pager': "",
            'ordenamiento': 0,
            'precioDesde': "",
            'precioHasta': ""
        }

        session.get('https://www.jumbo.com.ar/')
        session.headers.update({'Content-Type':
                                'application/json; charset=UTF-8'})

        response = session.post(
            'https://www.jumbo.com.ar/Comprar/HomeService.aspx/'
            'ObtenerArticulosPorDescripcionMarcaFamiliaLevex',
            json.dumps(params))

        containers = json.loads(json.loads(response.text)['d'])[
            'ResultadosBusquedaLevex']

        products = []

        for container in containers:
            name = container['DescripcionArticulo'].strip()
            price = Decimal(container['Precio'])
            sku = container['IdArticulo']
            stock = int(container['Stock'])
            picture_urls = ['https://images.jumbo.com.ar/JumboComprasArchivos/'
                            'Archivos/' + container['IdArchivoBig']]

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
                'ARS',
                sku=sku,
                picture_urls=picture_urls
            )

            products.append(p)

        return products
