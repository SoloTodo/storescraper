import base64
import json
import logging
import urllib
from collections import defaultdict
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import AIR_CONDITIONER, OVEN, REFRIGERATOR, \
    SPACE_HEATER, VACUUM_CLEANER, WASHING_MACHINE, WATER_HEATER

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Easy(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR,
            OVEN,
            VACUUM_CLEANER,
            WASHING_MACHINE,
            AIR_CONDITIONER,
            SPACE_HEATER,
            WATER_HEATER
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            # Electrohogar y climatización

            # Calefacción
            ['electrohogar-y-climatizacion/calefaccion/estufas-electricas',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas Eléctricas', 1],
            ['electrohogar-y-climatizacion/calefaccion/estufas-a-pellet',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas a Pellet', 1],
            ['electrohogar-y-climatizacion/calefaccion/estufas-a-gas',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas a Gas', 1],
            ['electrohogar-y-climatizacion/calefaccion/estufas-a-parafina',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas a Parafina', 1],
            ['electrohogar-y-climatizacion/calefaccion/estufas-a-lena',
             [SPACE_HEATER],
             'Inicio > Electrohogar > Calefacción > Estufas a leña', 1],

            # Calefont y Termos
            ['electrohogar-y-climatizacion/calefont-y-termos/calefont',
             [WATER_HEATER],
             'Inicio > Electrohogar y Climatización > Calefont y Termos > '
             'Calefont', 1],
            ['electrohogar-y-climatizacion/calefont-y-termos/termos-y-'
             'calderas', [WATER_HEATER],
             'Inicio > Electrohogar y Climatización > Calefont y Termos > '
             'Termos y calderas', 1],

            # Refrigeración
            ['electrohogar-y-climatizacion/refrigeracion/refrigeradores',
             [REFRIGERATOR],
             'Inicio > Electrohogar y Climatización > Refrigeración > '
             'Refrigeradores', 1],
            ['electrohogar-y-climatizacion/refrigeracion/freezer',
             [REFRIGERATOR],
             'Inicio > Electrohogar y Climatización > Refrigeración > '
             'Freezer', 1],
            ['electrohogar-y-climatizacion/refrigeracion/frigobar',
             [REFRIGERATOR],
             'Inicio > Electrohogar y Climatización > Refrigeración > '
             'Frigobar', 1],

            # Cocina
            ['electrohogar-y-climatizacion/cocina/hornos-empotrables',
             [OVEN],
             'Inicio > Electrohogar y Climatización > Cocina > '
             'Hornos Empotrables', 1],
            ['electrohogar-y-climatizacion/electrodomesticos/microondas',
             [OVEN],
             'Inicio > Electrohogar y Climatización > Cocina > Microondas', 1],

            # Lavado y planchado
            ['electrohogar-y-climatizacion/lavado-y-planchado/lavadoras',
             [WASHING_MACHINE],
             'Inicio > Electrohogar y Climatización > Lavado y planchado > '
             'Lavadoras', 1],
            ['electrohogar-y-climatizacion/lavado-y-planchado/secadoras',
             [WASHING_MACHINE],
             'Inicio > Electrohogar y Climatización > Lavado y planchado > '
             'Secadoras', 1],
            ['electrohogar-y-climatizacion/lavado-y-planchado/lavadoras-'
             'secadoras', [WASHING_MACHINE],
             'Inicio > Electrohogar y Climatización > Lavado y planchado > '
             'Lava - seca', 1],

            # Aspirado y limpieza
            ['electrohogar-y-climatizacion/aspirado-y-limpieza/aspiradoras',
             [VACUUM_CLEANER],
             'Inicio > Electrohogar y Climatización > Aspirado y limpieza > '
             'Aspiradoras', 1],
            ['electrohogar-y-climatizacion/aspirado-y-limpieza/robots-de-'
             'limpieza', [VACUUM_CLEANER],
             'Inicio > Electrohogar y Climatización > Aspirado y limpieza > '
             'Robots de limpieza', 1],

            # Electrodomésticos
            ['electrohogar-y-climatizacion/electrodomesticos/hornos-'
             'electricos', [OVEN],
             'Inicio > Electrohogar y Climatización > Electrodomésticos > '
             'Hornos eléctricos', 1],
            ['electrohogar-y-climatizacion/electrodomesticos/microondas',
             [OVEN],
             'Inicio > Electrohogar y Climatización > Electrodomésticos > '
             'Microondas', 1],

            # Ventilación
            ['electrohogar-y-climatizacion/ventilacion/aire-acondicionado-'
             'portatil', [AIR_CONDITIONER],
             'Inicio > Electrohogar y Climatización > Ventilación > '
             'Aire acondicionado portátil', 1],
            ['electrohogar-y-climatizacion/ventilacion/aire-acondicionado-'
             'split', [AIR_CONDITIONER],
             'Inicio > Electrohogar y Climatización > Ventilación > '
             'Aire Acondicionado split', 1],
            ['electrohogar-y-climatizacion/ventilacion/purificadores-y-'
             'humidificadores', [AIR_CONDITIONER],
             'Inicio > Electrohogar y Climatización > Ventilación > '
             'Purificadores y humidificadores', 1],
        ]

        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            offset = 0

            while True:
                if offset > 1000:
                    raise Exception('Page overflow')

                graphql_variables = {
                    "hideUnavailableItems": False,
                    "skusFilter": "FIRST_AVAILABLE",
                    "simulationBehavior": "default",
                    "installmentCriteria": "MAX_WITHOUT_INTEREST",
                    "productOriginVtex": False,
                    "map": "c,c,c",
                    "query": category_path,
                    "orderBy": "",
                    "from": offset,
                    "to": offset + 99,
                    "selectedFacets": [
                        {
                            "key": "c", "value": ""
                        }
                    ],
                    "facetsBehavior": "Static",
                    "categoryTreeBehavior": "default",
                    "withFacets": False
                }

                encoded_graphql_variables = base64.b64encode(
                    json.dumps(graphql_variables).encode(
                        'utf-8')).decode('utf-8')

                query_extensions = {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "6869499be99f20964918e2fe0d1166fdf"
                                      "6c006b1766085db9e5a6bc7c4b957e5"
                    },
                    "variables": encoded_graphql_variables
                }
                encoded_query_extensions = urllib.parse.quote(json.dumps(
                    query_extensions))
                endpoint = 'https://www.easy.cl/_v/segment/' \
                           'graphql/v1?extensions=' + encoded_query_extensions

                res = session.get(endpoint).json()
                raw_product_entries = res['data']['productSearch']['products']

                if not raw_product_entries:
                    if not offset:
                        logging.warning('Empty category: ' + category_path)
                    break

                for idx, prods_hit in enumerate(raw_product_entries):
                    product_url = 'https://www.easy.cl' + prods_hit['link']
                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': idx + 1
                    })

                offset += 100

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'
        product_urls = []

        base_prod_url = 'https://www.easy.cl/tienda/producto/{}'
        prods_url = 'https://www.easy.cl/api//prodeasy/_search'

        prods_data = {
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "must": [{
                                "bool": {
                                    "should": [{
                                        "function_score": {
                                            "query": {
                                                "multi_match": {
                                                    "query": keyword,
                                                    "fields": [
                                                        "name^1000",
                                                        "brand",
                                                        "cat_3.stop",
                                                        "partNumber"],
                                                    "type":"best_fields",
                                                    "operator":"and"}},
                                            "field_value_factor": {
                                                "field": "boost",
                                                "factor": 6}}}, {
                                        "multi_match": {
                                            "query": keyword,
                                            "fields": [
                                                "name^8",
                                                "cat_3.stop"],
                                            "type": "best_fields",
                                            "operator": "or"}}, {
                                        "span_first": {
                                            "match": {
                                                "span_term": {
                                                    "name.dym": keyword}},
                                            "end": 1,
                                            "boost": 2000}}],
                                    "minimum_should_match": "1"}}]}},
                    "boost_mode": "sum",
                    "score_mode": "max"}},
            "size": 450,
            "from": 0}

        prods_response = session.post(
            prods_url, data=json.dumps(prods_data))

        prods_json = json.loads(prods_response.text)
        prods_hits = prods_json['hits']['hits']

        if not prods_hits:
            return []

        for prods_hit in prods_hits:
            product_url = base_prod_url.format(prods_hit['_source']['url'])
            product_urls.append(product_url)

            if len(product_urls) == threshold:
                return product_urls

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        res = session.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        product_data = json.loads(soup.find(
            'template', {'data-varname': '__STATE__'}).text)

        base_json_keys = list(product_data.keys())

        if not base_json_keys:
            return []

        base_json_key = base_json_keys[0]
        product_specs = product_data[base_json_key]

        name = product_specs['productName']
        # Use the 'productReference' field and add the P to have the
        # same current key in the DB
        key = product_specs['productReference'] + 'P'
        # Store the new key to use in the SKU field for now, after running this
        # scraper, swap the keys and skus in the DB and edit this scraper to
        # make it finally correct
        sku = product_specs['productId']
        description = html_to_markdown(product_specs.get('description', None))

        pricing_key = '${}.items.0.sellers.0.commertialOffer'.format(
            base_json_key)
        pricing_data = product_data[pricing_key]

        normal_price = Decimal(pricing_data['Price'])

        offer_price_key = '{}.teasers.0.effects.parameters.0'.format(
            pricing_key)
        offer_price_json_value = product_data.get(offer_price_key, None)
        if offer_price_json_value:
            offer_price = Decimal(offer_price_json_value['value']) \
                / Decimal(100)
            if offer_price > normal_price:
                offer_price = normal_price
        else:
            offer_price = normal_price

        stock = pricing_data['AvailableQuantity']
        picture_list_key = '{}.items.0'.format(base_json_key)
        picture_list_node = product_data[picture_list_key]
        picture_ids = [x['id'] for x in picture_list_node['images']]

        picture_urls = []
        for picture_id in picture_ids:
            picture_node = product_data[picture_id]
            picture_urls.append(picture_node['imageUrl'].split('?')[0])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
